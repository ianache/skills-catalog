[[_TOC_]]

# Test Case Review Report

Este reporte cubre la evaluación del caso de prueba siguiente:

**Project ID**: [project_id] [project name]
**Issue ID**: [issue_id or test_case_id]
**Test Case**: [Test Case Code] [Test Case Name]

## Findings

Esta sección se debe organizar en base a los criterios de evaluación evaluados y el nivel de criticidad de los hallazgos: 
- Alta: son observaciones que afectan directamente la calidad del caso de prueba.
- Media: son observaciones que afectan indirectamente la calidad del caso de prueba.
- Baja: son observaciones menores relacionados con cuestiones de forma.

## Suggestions

Se debe aplicar las siguientes reglas:
- Si existe almenos un finding de criticidad Alta, se debe sugerir el rechazo (REJECT) del caso de prueba.
- Si existe almenos un finding de criticidad Media, se debe sugerir la modificación (MODIFY) del caso de prueba y requerir una siguiente revisión.
- Si existe almenos un finding de criticidad Baja y no existe ningun finding de criticidad Alta o Media, se debe aceptar (ACEPT) pero recomendar mejoras del caso de prueba.

## Approval Status

[ACEPT|REJECT|MODIFY]

## Next Steps

- Si el estado es REJECT, se debe solicitar al usuario que corrija el caso de prueba y vuelva a enviarlo para su revisión.
- Si el estado es MODIFY, se debe solicitar al usuario que corrija el caso de prueba y vuelva a enviarlo para su revisión.
- Si el estado es ACEPT, se puede continuar con el siguiente paso del flujo de trabajo.
- Incluir el nombre del author del test case.