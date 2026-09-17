# SdS TP3

## Compilación y ejecución

El proyecto utiliza CMake y requiere un compilador compatible con C++17.

Desde la raíz del repositorio:

```powershell
cmake -S . -B build
cmake --build build --config Release
```

El ejecutable se genera en:

```text
build/sds_tp3.exe
```

Para ejecutar una simulación con el tiempo máximo por defecto:

```powershell
./build/sds_tp3.exe
```

También se puede indicar el tiempo máximo en segundos como primer argumento:

```powershell
./build/sds_tp3.exe 30
```

Los argumentos son:

```text
tmax N configuracion_obstaculos archivo_de_estados
```

Por ejemplo:

```bash
./build/sds_tp3.exe 30 100 generated/mesa_vacia.txt generated/states.txt
```

Si no se indican argumentos, se usan `tmax=100`, `N=100`,
`generated/obstacles.txt` y `generated/states.txt`.

Al inicializarse, el programa utiliza `generated/obstacles.txt` como configuración de
obstáculos. Si el archivo no existe, genera una configuración aleatoria válida
y la guarda allí. Las ejecuciones siguientes cargan ese mismo archivo, por lo
que utilizan exactamente la misma configuración.

El formato del archivo es una línea por obstáculo:

```text
xk yk Rk
```

Un archivo vacío representa una mesa sin obstáculos, como la requerida para el
punto 1.1 del enunciado. El valor de `t90` se registra cuando se alcanza, pero
la simulación continúa hasta el tiempo máximo indicado.

La simulación también genera el estado del sistema en:

```text
generated/states.txt
```

El archivo contiene el tiempo, la posición, la velocidad y el estado de cada
partícula. El estado `1` representa una partícula fresca y `0` una partícula
usada.

## Experimentos y análisis

El motor C++ ejecuta una realización. Los experimentos y el análisis se
realizan con Python.

Para ejecutar varias realizaciones:

```bash
python scripts/run_experiments.py \
    --exe build/sds_tp3 \
    --config generated/mesa_vacia.txt generated/obstacles.txt \
    --n-values 50 100 200 \
    --repetitions 10 \
    --tmax 30
```

El runner genera `generated/experiments/results.csv` y un archivo de estados
por realización.

Para el punto 1.1, usar una configuración vacía, al menos 10 realizaciones,
`tmax=30` y varios valores de `N`:

```bash
python scripts/run_experiments.py \
    --exe build/sds_tp3 \
    --config generated/mesa_vacia.txt \
    --n-values 25 50 100 200 \
    --repetitions 10 \
    --tmax 30
```

Para el punto 1.2, usar `N=100`, al menos 5 realizaciones por configuración y
comparar contra la mesa vacía:

```bash
python scripts/run_experiments.py \
    --exe build/sds_tp3 \
    --config generated/mesa_vacia.txt generated/obstacles.txt \
    --n-values 100 \
    --repetitions 5 \
    --tmax 100
```

Para calcular el DCM y ajustar el coeficiente de difusión:

```bash
python scripts/analyze_states.py \
    generated/experiments/obstacles_N100_run1.txt \
    --plot \
    --fit-start 0 \
    --fit-end 10
```

El ajuste usa `DCM(t) = 4 D t` para el movimiento bidimensional.
`--fit-start` y `--fit-end` permiten seleccionar el tramo aproximadamente
lineal indicado por la teoría. El script genera el CSV del DCM y un PNG con
los puntos y el ajuste.

Para visualizar una simulación:

```bash
python scripts/animate_states.py \
    generated/experiments/obstacles_N100_run1.txt \
    --config generated/obstacles.txt
```

La reproducción usa por defecto `10` cuadros por segundo para que sea más
lenta. Se puede ajustar con `--fps`, por ejemplo:

```bash
python scripts/animate_states.py \
    generated/experiments/obstacles_N100_run1.txt \
    --config generated/obstacles.txt \
    --fps 5
```

Para guardar la animación como GIF:

```bash
python scripts/animate_states.py \
    generated/experiments/obstacles_N100_run1.txt \
    --config generated/obstacles.txt \
    --output generated/experiments/animation.gif
```

Las partículas frescas se muestran en azul y las usadas en rojo. El script
requiere `matplotlib` y, para guardar GIF, `pillow`.

Para resumir los resultados, calcular promedios y desvíos, estimar `D`,
calcular la correlación entre `D` y `t90`, y generar gráficos:

```bash
python scripts/analyze_experiments.py generated/experiments/results.csv
```

Se generan:

```text
summary.csv
diffusion.csv
presentation_summary.txt
runtime_vs_n.png
t90_vs_n.png
t90_by_configuration.png
diffusion_vs_t90.png
```

Los gráficos requieren `matplotlib`. Los archivos CSV se generan sin
dependencias externas.

Para validar una configuración de obstáculos:

```bash
python scripts/validate_config.py generated/obstacles.txt
```

Para ejecutar las cinco realizaciones de la competencia:

```bash
python scripts/run_competition.py \
    --exe build/sds_tp3 \
    --config generated/obstacles.txt
```

El runner usa `N=100`, `tmax=100 s` y genera los cinco estados junto con
`generated/competition/competition.csv`. Una configuración sin ningún `t90`
alcanzado queda marcada como no exitosa y se informa usando los goles promedio
a `tmax`.

## Flujo completo del TP

Para ejecutar automáticamente todos los experimentos y análisis:

```bash
python scripts/run_pipeline.py \
    --exe build/sds_tp3 \
    --obstacle-config generated/obstacles.txt
```

El pipeline ejecuta:

- punto 1.1: mesa vacía, los valores de `N` indicados y 10 realizaciones;
- puntos 1.2 y 1.3: mesa vacía y configuración final, `N=100` y 5 realizaciones;
- validación de configuraciones;
- análisis estadístico, DCM, `D` y gráficos;
- cinco realizaciones de competencia.

Los resultados quedan separados en:

```text
generated/tp_results/point_1_1/
generated/tp_results/point_1_2/
generated/tp_results/competition/
```

Para omitir la competencia durante una prueba:

```bash
python scripts/run_pipeline.py \
    --exe build/sds_tp3 \
    --skip-competition
```

La compilación recomendada es mediante CMake, que mantiene todos los archivos
intermedios dentro de `build/` y no genera archivos `.obj` en la raíz del
repositorio.