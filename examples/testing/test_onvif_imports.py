#!/usr/bin/env python3
"""
Script para verificar imports ONVIF disponibles
"""

print("Verificando imports ONVIF...")

# Test 1: Import básico
try:
    from onvif import ONVIFCamera
    print("✅ ONVIFCamera - OK")
except ImportError as e:
    print(f"❌ ONVIFCamera - Error: {e}")

# Test 2: Excepciones específicas
try:
    from onvif.exceptions import ONVIFAuthError, ONVIFError
    print("✅ Excepciones específicas - OK")
except ImportError as e:
    print(f"❌ Excepciones específicas - Error: {e}")

# Test 3: Excepciones genéricas
try:
    from onvif.exceptions import ONVIFError
    print("✅ ONVIFError genérico - OK")
except ImportError as e:
    print(f"❌ ONVIFError genérico - Error: {e}")

# Test 4: Verificar qué excepciones están disponibles
try:
    import onvif.exceptions
    print(f"✅ Módulo excepciones disponible: {dir(onvif.exceptions)}")
except ImportError as e:
    print(f"❌ Módulo excepciones - Error: {e}")

# Test 5: Crear instancia para verificar errores reales
try:
    from onvif import ONVIFCamera
    # Intentar con datos falsos para ver qué excepciones se lanzan
    cam = ONVIFCamera("1.1.1.1", 80, "fake", "fake")
    print("✅ Instancia creada")
except Exception as e:
    print(f"✅ Excepción capturada: {type(e).__name__}: {e}") 