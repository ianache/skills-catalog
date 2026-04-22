
# 1. Estrategia de Ejecución

- Usar @references/projects.md para determinar project_id en base a nombre de proyecto.

# Comportamiento Obligatorio (Secuencia Estricta)

Cuando el usuario mencione un ID de issue o TestCase para auditar, **debes seguir este orden**:

1.  **Identificación:** Identificar `project_id` e `issue_id`. Solicita el `project_id` al usuario si no lo tienes.
2.  **Obtención:** Llamar a la herramienta `get_gitlab_test_case` para obtener la especificación desde GitLab.
3.  **Understaning:** Si se indica una referencia #XXXX, se debe obtener el issue correspondiente y obtener su especificación (normalmente es la User Story specification a partir de la que se ha derivado el Test Case).
4.  **Evaluación (Audit):** Aplica tu razonamiento experto usando los Criterios de Evaluación QA al contenido obtenido. No busques una herramienta de evaluación; la evaluación la haces tú.
5.  **Informe Final (MANDATORIO):** Genera el resultado final utilizando **ESTRICTAMENTE esta plantilla**:
@evaluar_test_case/assets/report-template.md

# Criterios de Evaluación
- **Completitud:** ¿Hay precondiciones, pasos y resultados esperados?
- **Escenarios:** ¿Faltan casos negativos, límites o extremos?
- **Claridad:** ¿Los pasos son reproducibles?
- **Datos de Prueba:** ¿Se especifican los datos necesarios?