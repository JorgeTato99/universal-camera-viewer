"""
Panel de resultados para el escaneo de puertos.
Incluye tabla de resultados, vista de consola y información del escaneo.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
from datetime import datetime
import json
import csv
from ..scanning import PortResult, ScanResult

# cspell:disable
class ScanResultsPanel:
    """Panel que muestra los resultados del escaneo con UX mejorada."""
    
    def __init__(self, parent_container: tk.Widget):
        self.parent_container = parent_container
        self.current_scan_mode = "simple"
        self.results_tree: Optional[ttk.Treeview] = None
        
        # Estado de la vista
        self.show_console_view = False
        self.console_output = []
        self.console_text: Optional[tk.Text] = None
        self.toggle_view_btn: Optional[ttk.Button] = None
        
        # Variables de información y filtros
        self.scan_info_var = tk.StringVar(value="Sin escaneo realizado")
        self.filter_var = tk.StringVar()
        self.show_closed_var = tk.BooleanVar(value=True)
        self.show_open_var = tk.BooleanVar(value=True)
        
        # Estadísticas en tiempo real
        self.stats_open = tk.StringVar(value="0")
        self.stats_closed = tk.StringVar(value="0")
        self.stats_total = tk.StringVar(value="0")
        self.stats_time = tk.StringVar(value="0.0s")
        
        # Almacenar resultados para acceso posterior
        self.scan_results = []
        self.filtered_results = []
        
        self._create_panel()
    
    def _create_panel(self):
        """Crea el panel básico con mejoras de UX."""
        # Frame de resultados
        results_frame = ttk.LabelFrame(self.parent_container, text="Resultados del Escaneo")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=3)
        
        # Barra de herramientas superior
        self._create_toolbar(results_frame)
        
        # Barra de estadísticas
        self._create_stats_bar(results_frame)
        
        # Frame contenedor para las vistas
        self.views_container = ttk.Frame(results_frame)
        self.views_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crear ambas vistas
        self._create_table_view()
        self._create_console_view()
        
        # Mostrar vista de tabla por defecto
        self._show_table_view()
        
        # Crear sección de información mejorada
        self._create_info_section(results_frame)
    
    def _create_toolbar(self, parent_frame: tk.Widget):
        """Crea la barra de herramientas con controles de vista y filtros."""
        toolbar_frame = ttk.Frame(parent_frame)
        toolbar_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Lado izquierdo: Controles de vista
        left_controls = ttk.Frame(toolbar_frame)
        left_controls.pack(side=tk.LEFT)
        
        # Botón para alternar vista
        self.toggle_view_btn = ttk.Button(
            left_controls,
            text="🖥️ Vista Consola",
            command=self._toggle_view,
            width=15
        )
        self.toggle_view_btn.pack(side=tk.LEFT, padx=2)
        
        # Botón de exportar
        export_btn = ttk.Button(
            left_controls,
            text="📤 Exportar",
            command=self._show_export_menu,
            width=12
        )
        export_btn.pack(side=tk.LEFT, padx=2)
        
        # Separador
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        
        # Centro: Filtros
        filter_frame = ttk.Frame(toolbar_frame)
        filter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Búsqueda
        ttk.Label(filter_frame, text="🔍 Buscar:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=15)
        self.search_entry.pack(side=tk.LEFT, padx=(3, 8))
        self.filter_var.trace_add("write", self._apply_filters)
        
        # Filtros de estado
        ttk.Label(filter_frame, text="Mostrar:").pack(side=tk.LEFT)
        
        open_check = ttk.Checkbutton(
            filter_frame, 
            text="✅ Abiertos", 
            variable=self.show_open_var,
            command=self._apply_filters
        )
        open_check.pack(side=tk.LEFT, padx=3)
        
        closed_check = ttk.Checkbutton(
            filter_frame, 
            text="❌ Cerrados", 
            variable=self.show_closed_var,
            command=self._apply_filters
        )
        closed_check.pack(side=tk.LEFT, padx=3)
        
        # Lado derecho: Botón de limpiar filtros
        right_controls = ttk.Frame(toolbar_frame)
        right_controls.pack(side=tk.RIGHT)
        
        clear_filters_btn = ttk.Button(
            right_controls,
            text="🧹 Limpiar Filtros",
            command=self._clear_filters,
            width=15
        )
        clear_filters_btn.pack(side=tk.LEFT, padx=2)
    
    def _create_stats_bar(self, parent_frame: tk.Widget):
        """Crea la barra de estadísticas en tiempo real."""
        stats_frame = ttk.Frame(parent_frame)
        stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Fondo con color
        stats_bg = ttk.Frame(stats_frame, relief=tk.RIDGE, borderwidth=1)
        stats_bg.pack(fill=tk.X, padx=5)
        
        # Contenedor de estadísticas
        stats_container = ttk.Frame(stats_bg)
        stats_container.pack(fill=tk.X, padx=8, pady=3)
        
        # Estadística: Puertos abiertos
        open_frame = ttk.Frame(stats_container)
        open_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(open_frame, text="✅ Abiertos:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        ttk.Label(open_frame, textvariable=self.stats_open, font=("Arial", 8), foreground="#2e7d32").pack(side=tk.LEFT, padx=(3, 0))
        
        # Estadística: Puertos cerrados
        closed_frame = ttk.Frame(stats_container)
        closed_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(closed_frame, text="❌ Cerrados:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        ttk.Label(closed_frame, textvariable=self.stats_closed, font=("Arial", 8), foreground="#d32f2f").pack(side=tk.LEFT, padx=(3, 0))
        
        # Estadística: Total
        total_frame = ttk.Frame(stats_container)
        total_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(total_frame, text="📊 Total:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        ttk.Label(total_frame, textvariable=self.stats_total, font=("Arial", 8), foreground="#1976d2").pack(side=tk.LEFT, padx=(3, 0))
        
        # Estadística: Tiempo
        time_frame = ttk.Frame(stats_container)
        time_frame.pack(side=tk.RIGHT, padx=10)
        ttk.Label(time_frame, text="⏱️ Tiempo:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        ttk.Label(time_frame, textvariable=self.stats_time, font=("Arial", 8), foreground="#ff9800").pack(side=tk.LEFT, padx=(3, 0))
    
    def _show_export_menu(self):
        """Muestra el menú de exportación."""
        if not self.scan_results:
            messagebox.showwarning("Sin Datos", "No hay resultados para exportar")
            return
        
        # Crear menú contextual
        export_menu = tk.Menu(self.parent_container, tearoff=0)
        export_menu.add_command(label="📄 Exportar como CSV", command=lambda: self._export_results("csv"))
        export_menu.add_command(label="📋 Exportar como JSON", command=lambda: self._export_results("json"))
        export_menu.add_command(label="📝 Exportar como TXT", command=lambda: self._export_results("txt"))
        export_menu.add_separator()
        export_menu.add_command(label="📊 Generar Reporte HTML", command=self._generate_html_report)
        
        # Mostrar menú en la posición del cursor
        try:
            export_menu.tk_popup(
                self.parent_container.winfo_rootx() + 100,
                self.parent_container.winfo_rooty() + 100
            )
        finally:
            export_menu.grab_release()
    
    def _export_results(self, format_type: str):
        """Exporta los resultados en el formato especificado."""
        if format_type == "csv":
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Guardar resultados como CSV"
            )
            if filename:
                self._export_to_csv(filename)
        
        elif format_type == "json":
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Guardar resultados como JSON"
            )
            if filename:
                self._export_to_json(filename)
        
        elif format_type == "txt":
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Guardar resultados como TXT"
            )
            if filename:
                self._export_to_txt(filename)
    
    def _export_to_csv(self, filename: str):
        """Exporta resultados a CSV."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Puerto', 'Estado', 'Servicio', 'Tiempo (ms)', 'Banner'])
                
                for result in self.scan_results:
                    writer.writerow([
                        result.port,
                        "Abierto" if result.is_open else "Cerrado",
                        result.service_name or "Desconocido",
                        f"{result.response_time:.1f}" if result.response_time else "N/A",
                        result.banner or "No disponible"
                    ])
            
            messagebox.showinfo("Exportación Exitosa", f"Resultados exportados a:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"Error al exportar: {str(e)}")
    
    def _export_to_json(self, filename: str):
        """Exporta resultados a JSON."""
        try:
            data = {
                "scan_info": {
                    "timestamp": datetime.now().isoformat(),
                    "mode": self.current_scan_mode,
                    "total_ports": len(self.scan_results),
                    "open_ports": len([r for r in self.scan_results if r.is_open]),
                    "closed_ports": len([r for r in self.scan_results if not r.is_open])
                },
                "results": [
                    {
                        "port": result.port,
                        "is_open": result.is_open,
                        "service_name": result.service_name,
                        "response_time": result.response_time,
                        "banner": result.banner
                    }
                    for result in self.scan_results
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Exportación Exitosa", f"Resultados exportados a:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"Error al exportar: {str(e)}")
    
    def _export_to_txt(self, filename: str):
        """Exporta resultados a TXT."""
        try:
            with open(filename, 'w', encoding='utf-8') as txtfile:
                txtfile.write("REPORTE DE ESCANEO DE PUERTOS\n")
                txtfile.write("=" * 50 + "\n\n")
                txtfile.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                txtfile.write(f"Modo: {self.current_scan_mode.title()}\n")
                txtfile.write(f"Total de puertos: {len(self.scan_results)}\n")
                txtfile.write(f"Puertos abiertos: {len([r for r in self.scan_results if r.is_open])}\n")
                txtfile.write(f"Puertos cerrados: {len([r for r in self.scan_results if not r.is_open])}\n\n")
                
                txtfile.write("RESULTADOS DETALLADOS:\n")
                txtfile.write("-" * 30 + "\n")
                
                for result in self.scan_results:
                    status = "ABIERTO" if result.is_open else "CERRADO"
                    txtfile.write(f"Puerto {result.port}: {status}\n")
                    if result.service_name:
                        txtfile.write(f"  Servicio: {result.service_name}\n")
                    if result.response_time:
                        txtfile.write(f"  Tiempo: {result.response_time:.1f}ms\n")
                    if result.banner:
                        txtfile.write(f"  Banner: {result.banner}\n")
                    txtfile.write("\n")
            
            messagebox.showinfo("Exportación Exitosa", f"Resultados exportados a:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"Error al exportar: {str(e)}")
    
    def _generate_html_report(self):
        """Genera un reporte HTML completo."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            title="Guardar reporte HTML"
        )
        
        if not filename:
            return
        
        try:
            html_content = self._create_html_report()
            with open(filename, 'w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            messagebox.showinfo("Reporte Generado", f"Reporte HTML generado:\n{filename}")
            
            # Preguntar si quiere abrir el archivo
            if messagebox.askyesno("Abrir Reporte", "¿Desea abrir el reporte en el navegador?"):
                import webbrowser
                webbrowser.open(f"file://{filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar reporte: {str(e)}")
    
    def _create_html_report(self) -> str:
        """Crea el contenido HTML del reporte."""
        open_ports = [r for r in self.scan_results if r.is_open]
        closed_ports = [r for r in self.scan_results if not r.is_open]
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reporte de Escaneo de Puertos</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; border-radius: 8px; min-width: 120px; }}
                .stat-open {{ background-color: #d4edda; color: #155724; }}
                .stat-closed {{ background-color: #f8d7da; color: #721c24; }}
                .stat-total {{ background-color: #d1ecf1; color: #0c5460; }}
                .section {{ margin: 30px 0; }}
                .section h3 {{ color: #007bff; border-bottom: 1px solid #dee2e6; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
                th {{ background-color: #f8f9fa; font-weight: bold; }}
                .port-open {{ color: #28a745; font-weight: bold; }}
                .port-closed {{ color: #dc3545; }}
                .footer {{ text-align: center; margin-top: 40px; color: #6c757d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Reporte de Escaneo de Puertos</h1>
                    <p>Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-box stat-open">
                        <h3>{len(open_ports)}</h3>
                        <p>Puertos Abiertos</p>
                    </div>
                    <div class="stat-box stat-closed">
                        <h3>{len(closed_ports)}</h3>
                        <p>Puertos Cerrados</p>
                    </div>
                    <div class="stat-box stat-total">
                        <h3>{len(self.scan_results)}</h3>
                        <p>Total Escaneados</p>
                    </div>
                </div>
                
                <div class="section">
                    <h3>✅ Puertos Abiertos ({len(open_ports)})</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Puerto</th>
                                <th>Servicio</th>
                                <th>Tiempo (ms)</th>
                                <th>Banner</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for port in open_ports:
            html += f"""
                            <tr>
                                <td class="port-open">{port.port}</td>
                                <td>{port.service_name or 'Desconocido'}</td>
                                <td>{port.response_time:.1f if port.response_time else 'N/A'}</td>
                                <td>{port.banner or 'No disponible'}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h3>❌ Puertos Cerrados (Muestra)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Puerto</th>
                                <th>Servicio</th>
                                <th>Tiempo (ms)</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Mostrar solo los primeros 10 puertos cerrados para no saturar el reporte
        for port in closed_ports[:10]:
            html += f"""
                            <tr>
                                <td class="port-closed">{port.port}</td>
                                <td>{port.service_name or 'Desconocido'}</td>
                                <td>{port.response_time:.1f if port.response_time else 'N/A'}</td>
                            </tr>
            """
        
        if len(closed_ports) > 10:
            html += f"""
                            <tr>
                                <td colspan="3" style="text-align: center; font-style: italic; color: #6c757d;">
                                    ... y {len(closed_ports) - 10} puertos cerrados más
                                </td>
                            </tr>
            """
        
        html += f"""
                        </tbody>
                    </table>
                </div>
                
                <div class="footer">
                    <p>Reporte generado por Universal Visor - Módulo de Descubrimiento de Puertos</p>
                    <p>Modo de escaneo: {self.current_scan_mode.title()}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _apply_filters(self, *args):
        """Aplica los filtros de búsqueda y estado."""
        if not self.results_tree:
            return
        
        # Limpiar tabla
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Obtener criterios de filtro
        search_term = self.filter_var.get().lower()
        show_open = self.show_open_var.get()
        show_closed = self.show_closed_var.get()
        
        # Filtrar resultados
        self.filtered_results = []
        for result in self.scan_results:
            # Filtro por estado
            if result.is_open and not show_open:
                continue
            if not result.is_open and not show_closed:
                continue
            
            # Filtro por búsqueda
            if search_term:
                searchable_text = f"{result.port} {result.service_name or ''} {result.banner or ''}".lower()
                if search_term not in searchable_text:
                    continue
            
            self.filtered_results.append(result)
        
        # Mostrar resultados filtrados
        for result in self.filtered_results:
            self._add_result_to_tree(result)
        
        # Actualizar estadísticas de filtros
        self._update_filter_stats()
    
    def _update_filter_stats(self):
        """Actualiza las estadísticas considerando los filtros."""
        if not self.filtered_results:
            return
        
        open_count = len([r for r in self.filtered_results if r.is_open])
        closed_count = len([r for r in self.filtered_results if not r.is_open])
        total_count = len(self.filtered_results)
        
        # Si hay filtros activos, mostrar estadísticas filtradas
        if self.filter_var.get() or not (self.show_open_var.get() and self.show_closed_var.get()):
            self.stats_open.set(f"{open_count} (filtrado)")
            self.stats_closed.set(f"{closed_count} (filtrado)")
            self.stats_total.set(f"{total_count} (filtrado)")
        else:
            self.stats_open.set(str(open_count))
            self.stats_closed.set(str(closed_count))
            self.stats_total.set(str(total_count))
    
    def _clear_filters(self):
        """Limpia todos los filtros aplicados."""
        self.filter_var.set("")
        self.show_open_var.set(True)
        self.show_closed_var.set(True)
        self._apply_filters()

    def _create_table_view(self):
        """Crea la vista de tabla."""
        self.table_frame = ttk.Frame(self.views_container)
        self._setup_results_table(self.table_frame)
    
    def _create_console_view(self):
        """Crea la vista de consola."""
        self.console_frame = ttk.Frame(self.views_container)
        
        # Text widget para mostrar la salida de consola
        self.console_text = tk.Text(
            self.console_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff",
            state=tk.DISABLED
        )
        
        # Scrollbar para la consola
        console_scrollbar = ttk.Scrollbar(
            self.console_frame, 
            orient=tk.VERTICAL, 
            command=self.console_text.yview
        )
        self.console_text.configure(yscrollcommand=console_scrollbar.set)
        
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_info_section(self, parent_frame: tk.Widget):
        """Crea la sección de información."""
        info_frame = ttk.LabelFrame(parent_frame, text="Información del Escaneo")
        info_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Información del escaneo
        ttk.Label(info_frame, textvariable=self.scan_info_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Nota de ayuda
        help_label = ttk.Label(
            info_frame, 
            text="💡 Modo Avanzado: Doble clic en un puerto para ver URLs detalladas",
            font=("Arial", 8), 
            foreground="gray"
        )
        help_label.pack(anchor=tk.W, padx=10, pady=2)
    
    def _toggle_view(self):
        """Alterna entre vista de tabla y vista de consola."""
        if self.show_console_view:
            self._show_table_view()
        else:
            self._show_console_view()
    
    def _show_table_view(self):
        """Muestra la vista de tabla."""
        self.console_frame.pack_forget()
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        self.show_console_view = False
        if self.toggle_view_btn:
            self.toggle_view_btn.config(text="🖥️ Vista Consola")
    
    def _show_console_view(self):
        """Muestra la vista de consola."""
        self.table_frame.pack_forget()
        self.console_frame.pack(fill=tk.BOTH, expand=True)
        self.show_console_view = True
        if self.toggle_view_btn:
            self.toggle_view_btn.config(text="📊 Vista Tabla")
        
        # Actualizar contenido de consola
        self._update_console_display()
    
    def add_to_console(self, message: str, level: str = "INFO"):
        """
        Agrega un mensaje al buffer de consola.
        
        Args:
            message: Mensaje a agregar
            level: Nivel del mensaje (INFO, WARNING, ERROR, SUCCESS)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        self.console_output.append(formatted_message)
        
        # Mantener solo los últimos 1000 mensajes
        if len(self.console_output) > 1000:
            self.console_output = self.console_output[-1000:]
    
    def _update_console_display(self):
        """Actualiza la visualización de la consola."""
        if not self.console_text:
            return
        
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        
        for line in self.console_output:
            self.console_text.insert(tk.END, line + "\n")
            
            # Colorear según el nivel
            if "[ERROR]" in line:
                start_line = self.console_text.index(tk.END + "-2l linestart")
                end_line = self.console_text.index(tk.END + "-2l lineend")
                self.console_text.tag_add("error", start_line, end_line)
                self.console_text.tag_config("error", foreground="#ff6b6b")
            elif "[WARNING]" in line:
                start_line = self.console_text.index(tk.END + "-2l linestart")
                end_line = self.console_text.index(tk.END + "-2l lineend")
                self.console_text.tag_add("warning", start_line, end_line)
                self.console_text.tag_config("warning", foreground="#ffd93d")
            elif "[SUCCESS]" in line:
                start_line = self.console_text.index(tk.END + "-2l linestart")
                end_line = self.console_text.index(tk.END + "-2l lineend")
                self.console_text.tag_add("success", start_line, end_line)
                self.console_text.tag_config("success", foreground="#6bcf7f")
        
        self.console_text.config(state=tk.DISABLED)
        self.console_text.see(tk.END)
    
    def _setup_results_table(self, parent_frame):
        """Configura la tabla de resultados para modo simple."""
        columns = ("Puerto", "Estado", "Servicio", "Tiempo (ms)", "Banner")
        
        # Crear el Treeview
        self.results_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=8)
        
        # Configurar columnas
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)
        
        # Crear scrollbar
        self.results_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=self.results_scrollbar.set)
        
        # Empaquetar widgets
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar colores iniciales
        self._configure_table_colors()
        
        # Agregar evento de doble clic para mostrar detalles
        self.results_tree.bind("<Double-1>", self._on_result_double_click)
    
    def add_result_to_table(self, result: PortResult):
        """
        Agrega un resultado a la tabla con actualización de estadísticas en tiempo real.
        
        Args:
            result: Resultado del puerto escaneado
        """
        # Agregar a la lista de resultados
        self.scan_results.append(result)
        
        # Agregar a la tabla si pasa los filtros
        self._add_result_to_tree(result)
        
        # Actualizar estadísticas en tiempo real
        self._update_realtime_stats()
    
    def _add_result_to_tree(self, result: PortResult):
        """Agrega un resultado específico al árbol de resultados."""
        if not self.results_tree:
            return
        
        # Determinar valores para mostrar
        status_text = "✅ Abierto" if result.is_open else "❌ Cerrado"
        service_text = result.service_name or "Desconocido"
        time_text = f"{result.response_time:.1f}" if result.response_time else "N/A"
        banner_text = result.banner or "No disponible"
        
        # Insertar en la tabla
        item = self.results_tree.insert("", tk.END, values=(
            result.port,
            status_text,
            service_text,
            time_text,
            banner_text
        ))
        
        # Aplicar colores según el estado
        if result.is_open:
            self.results_tree.set(item, "Estado", "✅ Abierto")
            # Color verde para puertos abiertos
            self.results_tree.item(item, tags=("open",))
        else:
            self.results_tree.set(item, "Estado", "❌ Cerrado")
            # Color rojo para puertos cerrados
            self.results_tree.item(item, tags=("closed",))
    
    def _update_realtime_stats(self):
        """Actualiza las estadísticas en tiempo real."""
        open_count = len([r for r in self.scan_results if r.is_open])
        closed_count = len([r for r in self.scan_results if not r.is_open])
        total_count = len(self.scan_results)
        
        self.stats_open.set(str(open_count))
        self.stats_closed.set(str(closed_count))
        self.stats_total.set(str(total_count))
    
    def _configure_table_colors(self):
        """Configura los colores de la tabla según los tags."""
        if not self.results_tree:
            return
            
        # Configurar colores para los tags
        self.results_tree.tag_configure("open", background="#e8f5e8")  # Verde claro para abiertos
        self.results_tree.tag_configure("closed", background="#ffebee", foreground="#c62828")  # Rojo claro para cerrados
        
        # Colores adicionales para modo avanzado
        if self.current_scan_mode == "advanced":
            self.results_tree.tag_configure("auth_success", background="#d4edda")  # Verde más intenso para auth exitosa
            self.results_tree.tag_configure("auth_fail", background="#f8d7da")  # Rojo más intenso para auth fallida
    
    def _destroy_table_widgets(self):
        """Destruye correctamente la tabla y scrollbar para evitar duplicados."""
        if hasattr(self, 'results_tree') and self.results_tree:
            try:
                self.results_tree.destroy()
            except:
                pass
            self.results_tree = None
        
        if hasattr(self, 'results_scrollbar') and self.results_scrollbar:
            try:
                self.results_scrollbar.destroy()
            except:
                pass
            self.results_scrollbar = None

    def clear_results(self):
        """Limpia todos los resultados con confirmación."""
        if self.scan_results:
            if not messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar todos los resultados?"):
                return
        
        # Limpiar datos
        self.scan_results.clear()
        self.filtered_results.clear()
        self.console_output.clear()
        
        # Limpiar tabla de forma segura
        if hasattr(self, 'results_tree') and self.results_tree:
            try:
                for item in self.results_tree.get_children():
                    self.results_tree.delete(item)
            except:
                # Si hay error, recrear la tabla
                parent_frame = self.results_tree.master if self.results_tree else self.table_frame
                self._destroy_table_widgets()
                
                if self.current_scan_mode == "advanced":
                    self._setup_results_table_advanced(parent_frame)
                else:
                    self._setup_results_table(parent_frame)
        
        # Limpiar consola
        if self.console_text:
            self.console_text.config(state=tk.NORMAL)
            self.console_text.delete(1.0, tk.END)
            self.console_text.config(state=tk.DISABLED)
        
        # Resetear estadísticas
        self.stats_open.set("0")
        self.stats_closed.set("0")
        self.stats_total.set("0")
        self.stats_time.set("0.0s")
        
        # Resetear información
        self.scan_info_var.set("Sin escaneo realizado")
        
        # Limpiar filtros
        self._clear_filters()
    
    def set_scan_mode(self, mode: str):
        """
        Establece el modo de escaneo y reconfigura la tabla.
        
        Args:
            mode: Modo de escaneo ("simple" o "advanced")
        """
        # Si no hay cambio de modo, no hacer nada
        if self.current_scan_mode == mode:
            return
            
        self.current_scan_mode = mode
        
        # Solo reconfigurar si ya existe una tabla
        if hasattr(self, 'results_tree') and self.results_tree:
            # Guardar datos actuales si los hay
            current_data = []
            try:
                for item in self.results_tree.get_children():
                    current_data.append(self.results_tree.item(item, 'values'))
            except:
                current_data = []
            
            # Obtener el frame padre antes de destruir
            parent_frame = self.table_frame  # Usar el frame de tabla guardado
            
            # Destruir widgets de forma segura
            self._destroy_table_widgets()
            
            # Reconfigurar tabla según el modo
            if mode == "advanced":
                self._setup_results_table_advanced(parent_frame)
            else:
                self._setup_results_table(parent_frame)
                
            # Restaurar datos si los había (adaptándolos al formato correspondiente)
            for values in current_data:
                try:
                    if mode == "advanced":
                        # Adaptar datos al modo avanzado
                        if len(values) == 5:  # Formato simple -> avanzado
                            extended_values = list(values) + ["⏳ N/A", "No probado"]
                            self.results_tree.insert("", tk.END, values=extended_values)
                        else:  # Ya es formato avanzado
                            self.results_tree.insert("", tk.END, values=values)
                    else:
                        # Adaptar datos al modo simple
                        if len(values) > 5:  # Formato avanzado -> simple
                            simple_values = values[:5]  # Tomar solo las primeras 5 columnas
                            self.results_tree.insert("", tk.END, values=simple_values)
                        else:  # Ya es formato simple
                            self.results_tree.insert("", tk.END, values=values)
                except Exception as e:
                    print(f"Error restaurando datos: {e}")
                    continue
            
            # Reconfigurar colores después de restaurar datos
            self._configure_table_colors()
            
            # Reaplicar filtros si están activos
            if hasattr(self, 'filter_var') and self.filter_var.get():
                self._apply_filters()
    
    def _setup_results_table_advanced(self, parent_frame):
        """Configura la tabla de resultados para modo avanzado."""
        columns = ("Puerto", "Estado", "Servicio", "Tiempo (ms)", "Banner", "Auth", "Método")
        
        # Crear el Treeview
        self.results_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=8)
        
        # Configurar columnas con anchos específicos
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Puerto":
                self.results_tree.column(col, width=80)
            elif col == "Estado":
                self.results_tree.column(col, width=100)
            elif col == "Auth":
                self.results_tree.column(col, width=80)
            elif col == "Método":
                self.results_tree.column(col, width=180)
            elif col == "Tiempo (ms)":
                self.results_tree.column(col, width=100)
            elif col == "Banner":
                self.results_tree.column(col, width=200)
            else:
                self.results_tree.column(col, width=120)
        
        # Crear scrollbar
        self.results_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=self.results_scrollbar.set)
        
        # Empaquetar widgets
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar colores iniciales
        self._configure_table_colors()
        
        # Agregar evento de doble clic para mostrar detalles
        self.results_tree.bind("<Double-1>", self._on_result_double_click)
    
    def set_scan_info(self, info: str):
        """
        Establece la información del escaneo.
        
        Args:
            info: Información del escaneo
        """
        self.scan_info_var.set(info)

    def _on_result_double_click(self, event):
        """Maneja el evento de doble clic en un resultado."""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        # Obtener el item seleccionado
        item = selection[0]
        values = self.results_tree.item(item, 'values')
        
        if not values:
            return
        
        port = values[0]
        
        # Buscar el resultado correspondiente en los datos almacenados
        port_result = None
        for result in self.scan_results:
            if str(result.port) == str(port):
                port_result = result
                break
        
        if not port_result:
            return
        
        # Solo mostrar detalles si hay información
        if not hasattr(port_result, 'auth_tested') or not port_result.auth_tested:
            from tkinter import messagebox
            messagebox.showinfo("Sin detalles", f"No hay información de autenticación disponible para el puerto {port}")
            return
        
        self._show_url_details_dialog(port_result)
    
    def _show_url_details_dialog(self, port_result):
        """Muestra un diálogo con los detalles de autenticación según el tipo de puerto."""
        import tkinter as tk
        from tkinter import ttk
        
        dialog = tk.Toplevel(self.parent_container)
        dialog.title(f"Detalles de Autenticación - Puerto {port_result.port}")
        dialog.geometry("700x500")
        dialog.resizable(True, True)
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Información del puerto
        info_frame = ttk.LabelFrame(main_frame, text="Información del Puerto")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Puerto: {port_result.port}", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(info_frame, text=f"Servicio: {port_result.service_name}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(info_frame, text=f"Estado Auth: {'✅ Exitosa' if port_result.auth_success else '❌ Falló'}").pack(anchor=tk.W, padx=10, pady=2)
        if port_result.auth_method:
            ttk.Label(info_frame, text=f"Método: {port_result.auth_method}").pack(anchor=tk.W, padx=10, pady=2)
        
        # Determinar tipo de puerto para mostrar información apropiada
        is_http_port = port_result.port in [80, 443, 8000, 8080, 6667, 9000]
        is_dahua_sdk = port_result.port == 37777
        is_rtsp_port = port_result.port in [554, 5543]
        
        if is_http_port:
            # Para puertos HTTP, mostrar URLs válidas y probadas
            if hasattr(port_result, 'valid_urls') and port_result.valid_urls:
                valid_frame = ttk.LabelFrame(main_frame, text=f"🎯 URLs HTTP que FUNCIONARON ({len(port_result.valid_urls)})")
                valid_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                
                # Text widget con scroll para URLs válidas
                valid_text = tk.Text(valid_frame, height=8, wrap=tk.WORD)
                valid_scrollbar = ttk.Scrollbar(valid_frame, orient=tk.VERTICAL, command=valid_text.yview)
                valid_text.configure(yscrollcommand=valid_scrollbar.set)
                
                valid_text.insert(tk.END, "✅ URLs HTTP que respondieron correctamente:\n\n")
                for i, url in enumerate(port_result.valid_urls, 1):
                    valid_text.insert(tk.END, f"{i:2d}. ✅ {url}\n")
                
                valid_text.insert(tk.END, f"\n💡 Estas {len(port_result.valid_urls)} URL(s) aceptaron las credenciales y están disponibles para usar.")
                valid_text.insert(tk.END, "\n🔧 Métodos de autenticación exitosos: HTTP Digest Auth / HTTP Basic Auth")
                
                valid_text.config(state=tk.DISABLED)
                valid_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                valid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                # Mostrar URLs que no funcionaron (si las hay)
                if hasattr(port_result, 'tested_urls') and port_result.tested_urls:
                    valid_urls_set = set(port_result.valid_urls)
                    failed_urls = [url for url in port_result.tested_urls if url not in valid_urls_set]
                    
                    if failed_urls:
                        failed_frame = ttk.LabelFrame(main_frame, text=f"❌ URLs HTTP que NO funcionaron ({len(failed_urls)})")
                        failed_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                        
                        failed_text = tk.Text(failed_frame, height=6, wrap=tk.WORD)
                        failed_scrollbar = ttk.Scrollbar(failed_frame, orient=tk.VERTICAL, command=failed_text.yview)
                        failed_text.configure(yscrollcommand=failed_scrollbar.set)
                        
                        failed_text.insert(tk.END, "❌ URLs HTTP que rechazaron las credenciales:\n\n")
                        for i, url in enumerate(failed_urls, 1):
                            failed_text.insert(tk.END, f"{i:2d}. ❌ {url}\n")
                        
                        failed_text.insert(tk.END, f"\n⚠️ Estas {len(failed_urls)} URL(s) no respondieron correctamente con las credenciales.")
                        
                        failed_text.config(state=tk.DISABLED)
                        failed_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                        failed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            elif hasattr(port_result, 'tested_urls') and port_result.tested_urls:
                tested_frame = ttk.LabelFrame(main_frame, text=f"📋 Todas las URLs HTTP Probadas ({len(port_result.tested_urls)})")
                tested_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                
                # Text widget con scroll para URLs probadas
                tested_text = tk.Text(tested_frame, height=6, wrap=tk.WORD)
                tested_scrollbar = ttk.Scrollbar(tested_frame, orient=tk.VERTICAL, command=tested_text.yview)
                tested_text.configure(yscrollcommand=tested_scrollbar.set)
                
                tested_text.insert(tk.END, "Resultados de todas las URLs probadas:\n\n")
                for i, url in enumerate(port_result.tested_urls, 1):
                    # Marcar URLs válidas en verde
                    if hasattr(port_result, 'valid_urls') and any(url in valid_url for valid_url in port_result.valid_urls):
                        tested_text.insert(tk.END, f"{i:2d}. ✅ {url}\n")
                    else:
                        tested_text.insert(tk.END, f"{i:2d}. ❌ {url}\n")
                
                # Estadísticas
                valid_count = len(port_result.valid_urls) if hasattr(port_result, 'valid_urls') and port_result.valid_urls else 0
                failed_count = len(port_result.tested_urls) - valid_count
                tested_text.insert(tk.END, f"\n📊 Resumen: {valid_count} exitosas, {failed_count} fallidas de {len(port_result.tested_urls)} probadas")
                
                tested_text.config(state=tk.DISABLED)
                tested_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                tested_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Si no hay URLs válidas pero sí probadas (caso de fallo)
            elif hasattr(port_result, 'tested_urls') and port_result.tested_urls and not port_result.auth_success:
                failed_frame = ttk.LabelFrame(main_frame, text=f"❌ URLs HTTP Probadas - Todas Fallaron ({len(port_result.tested_urls)})")
                failed_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                
                failed_text = tk.Text(failed_frame, height=8, wrap=tk.WORD)
                failed_scrollbar = ttk.Scrollbar(failed_frame, orient=tk.VERTICAL, command=failed_text.yview)
                failed_text.configure(yscrollcommand=failed_scrollbar.set)
                
                failed_text.insert(tk.END, "❌ Ninguna URL HTTP respondió con las credenciales:\n\n")
                for i, url in enumerate(port_result.tested_urls, 1):
                    failed_text.insert(tk.END, f"{i:2d}. ❌ {url}\n")
                
                failed_text.insert(tk.END, f"\n⚠️ Las {len(port_result.tested_urls)} URLs probadas rechazaron las credenciales o no respondieron.")
                if port_result.auth_error:
                    failed_text.insert(tk.END, f"\n🔍 Error específico: {port_result.auth_error}")
                
                failed_text.config(state=tk.DISABLED)
                failed_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                failed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Si no hay información de URLs pero es puerto HTTP
            else:
                no_urls_frame = ttk.LabelFrame(main_frame, text="ℹ️ Información de Autenticación HTTP")
                no_urls_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                
                no_urls_text = tk.Text(no_urls_frame, height=8, wrap=tk.WORD)
                no_urls_scrollbar = ttk.Scrollbar(no_urls_frame, orient=tk.VERTICAL, command=no_urls_text.yview)
                no_urls_text.configure(yscrollcommand=no_urls_scrollbar.set)
                
                if port_result.auth_success:
                    no_urls_text.insert(tk.END, f"✅ Autenticación HTTP exitosa en puerto {port_result.port}\n\n")
                    no_urls_text.insert(tk.END, f"Servicio: {port_result.service_name}\n")
                    no_urls_text.insert(tk.END, f"Método: {port_result.auth_method}\n\n")
                    no_urls_text.insert(tk.END, "💡 Las credenciales fueron aceptadas por este servicio HTTP.\n")
                    no_urls_text.insert(tk.END, "📝 Nota: No se registraron URLs específicas, pero la autenticación fue exitosa.")
                else:
                    no_urls_text.insert(tk.END, f"❌ Autenticación HTTP fallida en puerto {port_result.port}\n\n")
                    no_urls_text.insert(tk.END, f"Servicio: {port_result.service_name}\n")
                    if port_result.auth_error:
                        no_urls_text.insert(tk.END, f"Error: {port_result.auth_error}\n\n")
                    no_urls_text.insert(tk.END, "⚠️ Las credenciales fueron rechazadas por este servicio HTTP.\n")
                    no_urls_text.insert(tk.END, "📝 Nota: No se pudieron probar URLs específicas o todas fallaron.")
                
                no_urls_text.config(state=tk.DISABLED)
                no_urls_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                no_urls_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        elif is_dahua_sdk:
            # Para puerto Dahua SDK (37777)
            dahua_frame = ttk.LabelFrame(main_frame, text="🎯 Dahua SDK - Puerto 37777")
            dahua_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            dahua_text = tk.Text(dahua_frame, height=10, wrap=tk.WORD)
            dahua_scrollbar = ttk.Scrollbar(dahua_frame, orient=tk.VERTICAL, command=dahua_text.yview)
            dahua_text.configure(yscrollcommand=dahua_scrollbar.set)
            
            if port_result.auth_success:
                dahua_text.insert(tk.END, f"✅ Autenticación Dahua SDK exitosa en puerto {port_result.port}\n\n")
                dahua_text.insert(tk.END, f"Servicio: {port_result.service_name}\n")
                dahua_text.insert(tk.END, f"Método: {port_result.auth_method}\n\n")
                dahua_text.insert(tk.END, "💡 Las credenciales fueron aceptadas por el servicio Dahua SDK.\n\n")
                dahua_text.insert(tk.END, "🔧 Este puerto permite:\n")
                dahua_text.insert(tk.END, "   • Acceso completo a la API de Dahua\n")
                dahua_text.insert(tk.END, "   • Control de PTZ (si está disponible)\n")
                dahua_text.insert(tk.END, "   • Configuración avanzada de la cámara\n")
                dahua_text.insert(tk.END, "   • Acceso a múltiples streams de video\n\n")
                dahua_text.insert(tk.END, "📝 Nota: Este es el puerto principal de administración de Dahua.")
            else:
                dahua_text.insert(tk.END, f"❌ Autenticación Dahua SDK fallida en puerto {port_result.port}\n\n")
                dahua_text.insert(tk.END, f"Servicio: {port_result.service_name}\n")
                if port_result.auth_error:
                    dahua_text.insert(tk.END, f"Error: {port_result.auth_error}\n\n")
                dahua_text.insert(tk.END, "⚠️ Las credenciales fueron rechazadas por el servicio Dahua SDK.\n\n")
                dahua_text.insert(tk.END, "🔍 Posibles causas:\n")
                dahua_text.insert(tk.END, "   • Credenciales incorrectas\n")
                dahua_text.insert(tk.END, "   • Usuario sin permisos de administrador\n")
                dahua_text.insert(tk.END, "   • Servicio SDK deshabilitado\n")
                dahua_text.insert(tk.END, "   • Firewall bloqueando la conexión")
            
            dahua_text.config(state=tk.DISABLED)
            dahua_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            dahua_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        elif is_rtsp_port:
            # Para puertos RTSP (554, 5543)
            rtsp_frame = ttk.LabelFrame(main_frame, text=f"📹 RTSP - Puerto {port_result.port}")
            rtsp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            rtsp_text = tk.Text(rtsp_frame, height=10, wrap=tk.WORD)
            rtsp_scrollbar = ttk.Scrollbar(rtsp_frame, orient=tk.VERTICAL, command=rtsp_text.yview)
            rtsp_text.configure(yscrollcommand=rtsp_scrollbar.set)
            
            if port_result.auth_success:
                rtsp_text.insert(tk.END, f"✅ Autenticación RTSP exitosa en puerto {port_result.port}\n\n")
                rtsp_text.insert(tk.END, f"Servicio: {port_result.service_name}\n")
                rtsp_text.insert(tk.END, f"Método: {port_result.auth_method}\n\n")
                
                # Mostrar URLs RTSP válidas si están disponibles
                if hasattr(port_result, 'valid_urls') and port_result.valid_urls:
                    rtsp_text.insert(tk.END, f"🎯 URLs RTSP que funcionaron ({len(port_result.valid_urls)}):\n\n")
                    for i, url in enumerate(port_result.valid_urls, 1):
                        rtsp_text.insert(tk.END, f"{i:2d}. ✅ {url}\n")
                    rtsp_text.insert(tk.END, f"\n💡 Estas {len(port_result.valid_urls)} URL(s) están disponibles para streaming.")
                else:
                    rtsp_text.insert(tk.END, "💡 Las credenciales fueron aceptadas por el servicio RTSP.\n")
                    rtsp_text.insert(tk.END, "📝 Nota: URLs específicas no registradas, pero la autenticación fue exitosa.")
                
                # Mostrar URLs probadas que no funcionaron
                if hasattr(port_result, 'tested_urls') and port_result.tested_urls:
                    valid_urls_set = set(port_result.valid_urls) if hasattr(port_result, 'valid_urls') and port_result.valid_urls else set()
                    failed_urls = [url for url in port_result.tested_urls if url not in valid_urls_set]
                    
                    if failed_urls:
                        rtsp_text.insert(tk.END, f"\n\n❌ URLs RTSP que NO funcionaron ({len(failed_urls)}):\n\n")
                        for i, url in enumerate(failed_urls, 1):
                            rtsp_text.insert(tk.END, f"{i:2d}. ❌ {url}\n")
                        rtsp_text.insert(tk.END, f"\n⚠️ Estas {len(failed_urls)} URL(s) rechazaron las credenciales o no respondieron.")
                
                rtsp_text.insert(tk.END, "\n\n🔧 Este puerto permite acceso a streams de video en tiempo real.")
            else:
                rtsp_text.insert(tk.END, f"❌ Autenticación RTSP fallida en puerto {port_result.port}\n\n")
                rtsp_text.insert(tk.END, f"Servicio: {port_result.service_name}\n")
                if port_result.auth_error:
                    rtsp_text.insert(tk.END, f"Error: {port_result.auth_error}\n\n")
                
                # Mostrar URLs probadas si están disponibles
                if hasattr(port_result, 'tested_urls') and port_result.tested_urls:
                    rtsp_text.insert(tk.END, f"📋 URLs RTSP probadas ({len(port_result.tested_urls)}):\n\n")
                    for i, url in enumerate(port_result.tested_urls, 1):
                        rtsp_text.insert(tk.END, f"{i:2d}. ❌ {url}\n")
                    rtsp_text.insert(tk.END, f"\n⚠️ Las {len(port_result.tested_urls)} URLs probadas rechazaron las credenciales.")
                else:
                    rtsp_text.insert(tk.END, "⚠️ Las credenciales fueron rechazadas por el servicio RTSP.")
            
            rtsp_text.config(state=tk.DISABLED)
            rtsp_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            rtsp_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            # Para otros tipos de puertos, mostrar información general
            info_text = tk.Text(main_frame, height=10, wrap=tk.WORD)
            info_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=info_text.yview)
            info_text.configure(yscrollcommand=info_scrollbar.set)
            
            if port_result.auth_success:
                info_text.insert(tk.END, f"✅ Autenticación exitosa en puerto {port_result.port}\n\n")
                info_text.insert(tk.END, f"Servicio: {port_result.service_name}\n")
                info_text.insert(tk.END, f"Método: {port_result.auth_method}\n\n")
                info_text.insert(tk.END, "💡 Las credenciales fueron aceptadas por este servicio.")
            else:
                info_text.insert(tk.END, f"❌ Autenticación fallida en puerto {port_result.port}\n\n")
                info_text.insert(tk.END, f"Servicio: {port_result.service_name}\n")
                if port_result.auth_error:
                    info_text.insert(tk.END, f"Error: {port_result.auth_error}\n\n")
                info_text.insert(tk.END, "⚠️ Las credenciales fueron rechazadas por este servicio.")
            
            info_text.config(state=tk.DISABLED)
            info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botón cerrar
        ttk.Button(main_frame, text="Cerrar", command=dialog.destroy).pack(pady=10) 