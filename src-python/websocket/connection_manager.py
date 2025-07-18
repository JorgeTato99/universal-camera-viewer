"""
Gestor de conexiones WebSocket
"""

from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Representa una conexión WebSocket individual."""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = datetime.utcnow()
        self.rooms: Set[str] = set()
        
    async def send_json(self, data: dict) -> bool:
        """
        Enviar datos JSON a través del WebSocket.
        
        Args:
            data: Diccionario a enviar
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Verificar estado del WebSocket antes de enviar
            if hasattr(self.websocket, 'client_state'):
                # 0 = CONNECTING, 1 = CONNECTED, 2 = DISCONNECTED
                if self.websocket.client_state.value != 1:
                    logger.debug(f"WebSocket no conectado para {self.client_id}, ignorando mensaje")
                    return False
            
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            # Solo loggear si no es un error esperado de desconexión
            error_msg = str(e)
            if "WebSocket" in error_msg or "Cannot call" in error_msg or "close message" in error_msg:
                logger.debug(f"WebSocket cerrado para {self.client_id}: {error_msg}")
            else:
                logger.error(f"Error enviando a {self.client_id}: {e}")
            return False
    
    async def send_text(self, message: str) -> bool:
        """
        Enviar texto a través del WebSocket.
        
        Args:
            message: Mensaje a enviar
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Verificar estado del WebSocket antes de enviar
            if hasattr(self.websocket, 'client_state'):
                if self.websocket.client_state.value != 1:
                    logger.debug(f"WebSocket no conectado para {self.client_id}, ignorando mensaje")
                    return False
            
            await self.websocket.send_text(message)
            return True
        except Exception as e:
            # Solo loggear si no es un error esperado de desconexión
            error_msg = str(e)
            if "WebSocket" in error_msg or "Cannot call" in error_msg or "close message" in error_msg:
                logger.debug(f"WebSocket cerrado para {self.client_id}: {error_msg}")
            else:
                logger.error(f"Error enviando a {self.client_id}: {e}")
            return False


class ConnectionManager:
    """Gestor global de conexiones WebSocket."""
    
    def __init__(self):
        # Conexiones activas por client_id
        self.active_connections: Dict[str, WebSocketConnection] = {}
        # Salas/rooms para broadcast
        self.rooms: Dict[str, Set[str]] = {}
        # Métricas
        self.total_connections = 0
        self.total_messages_sent = 0
        
    async def connect(self, websocket: WebSocket, client_id: str) -> WebSocketConnection:
        """
        Conectar un nuevo cliente WebSocket.
        
        Args:
            websocket: WebSocket de FastAPI
            client_id: ID único del cliente
            
        Returns:
            WebSocketConnection: Conexión creada
        """
        await websocket.accept()
        
        connection = WebSocketConnection(websocket, client_id)
        self.active_connections[client_id] = connection
        self.total_connections += 1
        
        logger.info(f"Cliente conectado: {client_id}")
        logger.info(f"Total conexiones activas: {len(self.active_connections)}")
        
        # Enviar mensaje de bienvenida
        await connection.send_json({
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        return connection
    
    async def disconnect(self, client_id: str):
        """
        Desconectar un cliente.
        
        Args:
            client_id: ID del cliente a desconectar
        """
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            
            # Eliminar de todas las salas
            for room in list(connection.rooms):
                await self.leave_room(client_id, room)
            
            # Eliminar conexión
            del self.active_connections[client_id]
            
            logger.info(f"Cliente desconectado: {client_id}")
            logger.info(f"Total conexiones activas: {len(self.active_connections)}")
    
    async def join_room(self, client_id: str, room: str):
        """
        Unir cliente a una sala/room.
        
        Args:
            client_id: ID del cliente
            room: Nombre de la sala
        """
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            connection.rooms.add(room)
            
            if room not in self.rooms:
                self.rooms[room] = set()
            self.rooms[room].add(client_id)
            
            logger.info(f"Cliente {client_id} unido a sala {room}")
            
            # Notificar al cliente
            await connection.send_json({
                "type": "room_joined",
                "room": room,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
    
    async def leave_room(self, client_id: str, room: str):
        """
        Remover cliente de una sala/room.
        
        Args:
            client_id: ID del cliente
            room: Nombre de la sala
        """
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            connection.rooms.discard(room)
            
            if room in self.rooms:
                self.rooms[room].discard(client_id)
                if not self.rooms[room]:
                    del self.rooms[room]
            
            logger.info(f"Cliente {client_id} salió de sala {room}")
    
    async def send_personal_message(self, message: dict, client_id: str) -> bool:
        """
        Enviar mensaje a un cliente específico.
        
        Args:
            message: Mensaje a enviar
            client_id: ID del cliente destinatario
            
        Returns:
            bool: True si se envió correctamente
        """
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            success = await connection.send_json(message)
            if success:
                self.total_messages_sent += 1
            return success
        return False
    
    async def broadcast(self, message: dict, room: Optional[str] = None):
        """
        Enviar mensaje a todos los clientes o a una sala específica.
        
        Args:
            message: Mensaje a enviar
            room: Sala opcional para broadcast dirigido
        """
        if room:
            # Broadcast a sala específica
            if room in self.rooms:
                tasks = []
                for client_id in self.rooms[room]:
                    if client_id in self.active_connections:
                        connection = self.active_connections[client_id]
                        tasks.append(connection.send_json(message))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                sent = sum(1 for r in results if r is True)
                self.total_messages_sent += sent
                
                logger.debug(f"Broadcast a sala {room}: {sent}/{len(tasks)} mensajes enviados")
        else:
            # Broadcast global
            tasks = []
            for connection in self.active_connections.values():
                tasks.append(connection.send_json(message))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sent = sum(1 for r in results if r is True)
            self.total_messages_sent += sent
            
            logger.debug(f"Broadcast global: {sent}/{len(tasks)} mensajes enviados")
    
    def get_connection(self, client_id: str) -> Optional[WebSocketConnection]:
        """Obtener conexión por client_id."""
        return self.active_connections.get(client_id)
    
    def get_stats(self) -> dict:
        """Obtener estadísticas del manager."""
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.total_connections,
            "total_messages_sent": self.total_messages_sent,
            "rooms": {room: len(clients) for room, clients in self.rooms.items()},
            "clients": list(self.active_connections.keys())
        }


# Instancia global del manager
manager = ConnectionManager()