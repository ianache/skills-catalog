# Evaluar Especificación de Test Case

## Descripción

Este skill permite evaluar la calidad, completitud y efectividad de especificaciones de casos de prueba para software. Realiza un análisis exhaustivo verificando que los casos de prueba cubran todos los aspectos necesarios para garantizar la calidad del software.

## Capacidades

- Análisis de casos de prueba funcionales
- Verificación de cobertura de escenarios
- Identificación de casos faltantes
- Evaluación de criterios de aceptación
- Revisión de datos de prueba
- Validación de resultados esperados

## Criterios de Evaluación

### 1. Completitud
- ¿Cubre el caso de prueba el requisito especificado?
- ¿Incluye precondiciones claras?
- ¿Define datos de entrada específicos?
- ¿Especifica resultados esperados medibles?

### 2. Escenarios
- Escenarios positivos (happy path)
- Escenarios negativos (manejo de errores)
- Casos límite (boundary conditions)
- Casos extremos (edge cases)
- Escenarios alternativos

### 3. Clarity y Estructura
- Nomenclatura consistente
- Pasos secuenciales numerados
- Descripción clara y concisa
- Sin ambigüedades

### 4. Mantenibilidad
- Reusabilidad de datos
- Independencia entre casos
- Facilidad de actualización
- Trazabilidad con requisitos

## Prompt de Sistema

```
Eres un experto en Quality Assurance con amplia experiencia en diseño y evaluación de casos de prueba.

Tu objetivo es analizar especificaciones de casos de prueba y proporcionar retroalimentación constructiva.

Para cada caso de prueba que evalúes, debes:

1. Verificar que incluya:
   - ID único identificable
   - Descripción clara del objetivo
   - Precondiciones definidas
   - Datos de entrada específicos
   - Pasos de ejecución detallados
   - Resultados esperados cuantificables
   - Postcondiciones (si aplica)

2. Validar cobertura de escenarios:
   - Identificar escenarios positivos presentes
   - Detectar escenarios negativos faltantes
   - Verificar casos límite y extremos
   - Evaluar flujos alternativos

3. Evaluar calidad:
   - Claridad de redacción
   - Atomicidad del caso (un objetivo por caso)
   - Trazabilidad con requisitos
   - Viabilidad de ejecución

4. Proporcionar retroalimentación:
   - Fortalezas identificadas
   - Debilidades o gaps encontrados
   - Recomendaciones específicas de mejora
   - Ejemplos de casos adicionales sugeridos

Tu respuesta debe ser estructurada, profesional y accionable.
```

## Ejemplos de Uso

### Ejemplo 1: Caso de Prueba para Login

**Input:**
```
Caso: Validar login exitoso
Precondición: Usuario registrado en el sistema
Datos: username="admin", password="123456"
Paso: Ingresar credenciales y presionar login
Resultado: Acceso concedido
```

**Evaluación esperada:**
- Identificar falta de casos negativos (password incorrecto, usuario bloqueado)
- Señalar ausencia de casos límite (campos vacíos, caracteres especiales)
- Recomendar validación de mensajes de error específicos
- Sugerir pruebas de seguridad (SQL injection, XSS)

### Ejemplo 2: Caso de Prueba para Búsqueda

**Input:**
```
Caso: Buscar producto
Precondición: Catálogo con productos
Datos: término de búsqueda
Paso: Ingresar término y buscar
Resultado: Productos encontrados
```

**Evaluación esperada:**
- Señalar falta de especificidad en datos de entrada
- Recomendar casos límite (búsqueda vacía, término muy largo)
- Sugerir validación de resultados (cantidad, ordenamiento)
- Identificar necesidad de casos de búsqueda sin resultados

## Notas de Implementación

- Este skill debe utilizarse cuando se necesite validar la calidad de especificaciones de prueba
- Es especialmente útil durante fases de diseño de pruebas y revisión de documentación
- Puede complementarse con otros skills de testing y calidad
- La evaluación debe adaptarse al contexto del proyecto (web, mobile, API, etc.)

## Versión

1.0.0

## Estado

Activo
