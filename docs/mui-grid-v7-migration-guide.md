# 🔧 Guía de Migración: Material-UI Grid v5 → v7

## 🤔 El Problema Común

Muchos modelos de IA (incluido yo mismo) suelen confundirse con la sintaxis de Material-UI Grid porque:

1. **La mayoría de la documentación y ejemplos en internet** todavía usan la sintaxis v5
2. **Los datos de entrenamiento** de los modelos suelen contener más ejemplos de v5 que v7
3. **La migración fue significativa** y cambió la API completamente

> **Nota**: La inconsistencia MediaMTXPath `id` vs `path_id` mencionada anteriormente en este documento ha sido resuelta mediante el uso de alias en Pydantic. Ver `docs/mediamtx-id-inconsistency-solution.md` para más detalles.

---

## ❌ Sintaxis Antigua (v5)

```jsx
import { Grid } from '@mui/material';

// INCORRECTO en v7
<Grid container spacing={2}>
  <Grid item xs={12} md={6} lg={4}>
    <Content />
  </Grid>
</Grid>
```

## ✅ Sintaxis Nueva (v7)

```jsx
import { Grid } from '@mui/material';

// CORRECTO en v7
<Grid container spacing={2}>
  <Grid size={{ xs: 12, md: 6, lg: 4 }}>
    <Content />
  </Grid>
</Grid>
```

## 🔑 Cambios Clave

### 1. **Eliminación del prop `item`**

- **v5**: `<Grid item>`
- **v7**: `<Grid>` (sin `item`)

### 2. **Nuevo prop `size`**

- **v5**: `xs={12} md={6}`
- **v7**: `size={{ xs: 12, md: 6 }}`

### 3. **NO usar Grid2**

- ❌ `import Grid2 from '@mui/material/Unstable_Grid2'`
- ✅ `import { Grid } from '@mui/material'`

## 🚨 Errores Comunes

### Error 1: "Property 'item' does not exist"

```jsx
// ❌ INCORRECTO
<Grid item xs={12}>

// ✅ CORRECTO
<Grid size={{ xs: 12 }}>
```

### Error 2: "Property 'xs' does not exist"

```jsx
// ❌ INCORRECTO
<Grid xs={12} md={6}>

// ✅ CORRECTO
<Grid size={{ xs: 12, md: 6 }}>
```

### Error 3: Intentar usar Grid2

```jsx
// ❌ INCORRECTO - NO uses Grid2
import Grid2 from '@mui/material/Unstable_Grid2';
<Grid2 size={{ xs: 12 }}>

// ✅ CORRECTO - Usa Grid normal
import { Grid } from '@mui/material';
<Grid size={{ xs: 12 }}>
```

## 💡 Cómo el Usuario Me Corrigió

Cuando intenté usar `Grid2` o `Unstable_Grid2`, el usuario me aclaró:

> "No, no debes usar Grid2, la importación es la misma, simplemente que la versión más nueva es la 7.2"

La clave es:

- **Misma importación**: `import { Grid } from '@mui/material'`
- **Nueva sintaxis**: `size` en lugar de props individuales
- **Sin Grid2**: No usar versiones "unstable" o "Grid2"

## 📋 Ejemplos de Migración

### Ejemplo 1: Grid Simple

```jsx
// v5
<Grid item xs={12}>

// v7
<Grid size={12}>
```

### Ejemplo 2: Grid Responsive

```jsx
// v5
<Grid item xs={12} sm={6} md={4} lg={3}>

// v7
<Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
```

### Ejemplo 3: Grid Container

```jsx
// v5 y v7 - El container NO cambia
<Grid container spacing={2}>
```

## 🎯 Resumen para Modelos de IA

Si estás trabajando con Material-UI v7+:

1. **NO uses** la palabra `item` en Grid
2. **USA** `size={{ xs: 12, md: 6 }}` para breakpoints
3. **IMPORTA** desde `@mui/material`, no de `Unstable_Grid2`
4. **VERIFICA** la versión en package.json antes de escribir código

## 📦 Verificar Versión

```json
// package.json
{
  "dependencies": {
    "@mui/material": "^7.2.0" // v7 = usa sintaxis nueva
  }
}
```

---

**Nota**: Esta guía fue creada después de experimentar estos errores en primera persona. Si eres un modelo de IA leyendo esto, usa la sintaxis v7 cuando veas Material-UI 7.x en el proyecto.
