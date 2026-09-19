#!/usr/bin/env python3
"""Actualizar la copia de WSL con respaldo externo y avance normal de Git."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PRACTICAS = 'unidad-01-introduccion-ia/practicas'
CARPETAS = (
    'practica-01-tablas-de-verdad',
    'practica-02-sistema-examen',
    'practica-03-sistema-examen-lista-oficial',
    'practica-04-diagnostico-equipo',
    'practica-05-diagnostico-equipo-reporte',
    'practica-06-sistema-experto-salud',
    'practica-07-sistema-experto-salud-mejorado',
    'practica-08-conexion-mongodb',
    'practica-09-conexion-mongodb-atlas',
    'practica-10-agente-climatizacion',
)
ANTIGUOS = (
    'practicas_revision.zip', 'practicas_con_interfaz.zip',
    'instalar_practica_08_web.sh', 'instalar_practica_09_atlas.sh',
    'instalar_interfaces_practicas.sh',
)
ALCANCE = (
    PRACTICAS, 'unidad-01-introduccion-ia/practicas_respaldo',
    'README.md', '.gitignore', 'iniciar_practica_web.sh',
    'sincronizar_practicas.py', 'CLAUDE.md', '.claude',
    *ANTIGUOS, *(nombre + ':Zone.Identifier' for nombre in ANTIGUOS),
)
REPOSITORIO = 'Einar-520/Practicas-Fundamentos_IA'


def git(raiz, *argumentos, comprobar=True):
    proceso = subprocess.run(['git', '-C', str(raiz), *argumentos],
                             capture_output=True, text=True)
    if comprobar and proceso.returncode:
        # Los comandos empleados aquí no imprimen credenciales ni archivos.
        raise RuntimeError(proceso.stderr.strip() or 'Git no pudo completar la operación.')
    return proceso


def existe(ruta):
    return ruta.exists() or ruta.is_symlink()


def retirar(ruta):
    if ruta.is_symlink() or ruta.is_file():
        ruta.unlink()
    elif ruta.is_dir():
        shutil.rmtree(ruta)


def comprobar_proyecto(raiz):
    real = Path(git(raiz, 'rev-parse', '--show-toplevel').stdout.strip()).resolve()
    if raiz != real:
        raise RuntimeError('Ejecuta el comando desde la raíz del proyecto fundamentos-ia.')
    remoto = git(raiz, 'remote', 'get-url', 'origin').stdout.strip().removesuffix('.git').rstrip('/')
    if remoto not in (f'https://github.com/{REPOSITORIO}', f'git@github.com:{REPOSITORIO}',
                       f'ssh://git@github.com/{REPOSITORIO}'):
        raise RuntimeError('El remoto origin no corresponde a Einar-520/Practicas-Fundamentos_IA.')
    if git(raiz, 'symbolic-ref', '--short', 'HEAD').stdout.strip() != 'main':
        raise RuntimeError('Selecciona la rama main antes de actualizar las prácticas.')
    for nombre in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD',
                   'rebase-merge', 'rebase-apply', 'index.lock'):
        ruta = Path(git(raiz, 'rev-parse', '--git-path', nombre).stdout.strip())
        if existe(raiz / ruta):
            raise RuntimeError('Finaliza la operación de Git pendiente antes de actualizar.')
    if git(raiz, 'config', '--bool', 'core.sparseCheckout', comprobar=False).stdout.strip() == 'true':
        raise RuntimeError('Esta actualización necesita una copia completa, sin sparse checkout.')
    anterior = git(raiz, 'rev-parse', 'HEAD').stdout.strip()
    destino = git(raiz, 'rev-parse', 'refs/remotes/origin/main').stdout.strip()
    if git(raiz, 'merge-base', '--is-ancestor', anterior, destino, comprobar=False).returncode:
        raise RuntimeError('Hay commits locales que no están en origin/main. Consérvalos e intégralos antes de actualizar; no se ha borrado nada.')
    archivos = set(git(raiz, 'ls-tree', '-r', '--name-only', destino, '--', PRACTICAS).stdout.splitlines())
    esperados = {f'{PRACTICAS}/{carpeta}/templates/index.html' for carpeta in CARPETAS[:9]}
    esperados.add(f'{PRACTICAS}/practica-10-agente-climatizacion/10_agente_climatizacion.py')
    if not esperados.issubset(archivos):
        raise RuntimeError('origin/main no contiene las diez prácticas completas. Ejecuta git fetch origin main.')
    if any(Path(ruta).name == '.env' for ruta in archivos):
        raise RuntimeError('La versión remota contiene un .env versionado. No se reemplazará tu configuración.')
    for relativo in ALCANCE:
        for padre in (raiz / relativo).parents:
            if padre == raiz:
                break
            if padre.is_symlink():
                raise RuntimeError('Una carpeta que se actualizaría es un enlace simbólico. No se ha modificado nada.')
    return anterior, destino


def restaurar_configuracion(raiz, respaldo):
    for carpeta in CARPETAS:
        anterior = respaldo / PRACTICAS / carpeta
        actual = raiz / PRACTICAS / carpeta
        for configuracion in anterior.glob('.env*'):
            if configuracion.name == '.env.example':
                continue
            if configuracion.is_file() or configuracion.is_symlink():
                copia = actual / configuracion.name
                shutil.copy2(configuracion, copia, follow_symlinks=False)
                if not copia.is_symlink():
                    copia.chmod(0o600)
        # Un entorno propio de una práctica también sigue siendo local.
        for nombre in ('.venv', 'venv'):
            entorno = anterior / nombre
            if entorno.is_symlink():
                (actual / nombre).symlink_to(os.readlink(entorno))
            elif entorno.is_dir():
                shutil.copytree(entorno, actual / nombre, symlinks=True)


def sincronizar(raiz):
    anterior, destino = comprobar_proyecto(raiz)
    contenedor = raiz.parent / f'{raiz.name}-respaldos'
    if contenedor.is_symlink():
        raise RuntimeError('La carpeta de respaldos no puede ser un enlace simbólico.')
    contenedor.mkdir(mode=0o700, exist_ok=True)
    respaldo = Path(tempfile.mkdtemp(prefix='sincronizacion-', dir=contenedor))
    indice = Path(git(raiz, 'rev-parse', '--git-path', 'index').stdout.strip())
    indice = raiz / indice
    shutil.copy2(indice, respaldo / 'indice-git-original')
    (respaldo / 'commit-original.txt').write_text(anterior + '\n')
    (respaldo / 'LEEME.txt').write_text(
        'Respaldo privado anterior a la actualización. Puede contener tu .env.\n'
        'Los archivos conservan las rutas relativas del proyecto.\n'
        'indice-git-original conserva también qué cambios estaban preparados en Git.\n'
        'No copies este respaldo dentro del repositorio ni lo subas a GitHub.\n')
    print(f'Respaldo fuera del proyecto: {respaldo}', flush=True)
    movidos = []
    preparado = False
    try:
        for relativo in ALCANCE:
            origen = raiz / relativo
            if existe(origen):
                copia = respaldo / relativo
                copia.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(origen), str(copia))
                movidos.append(relativo)
        preparado = True
        # Solo se restablece el alcance respaldado. Los demás archivos y su
        # selección en el índice no se modifican mediante estos comandos.
        git(raiz, 'rm', '-r', '-f', '--cached', '--ignore-unmatch', '--', *ALCANCE)
        versionados = git(raiz, 'ls-tree', '-r', '--name-only', anterior, '--', *ALCANCE).stdout.splitlines()
        if versionados:
            git(raiz, 'restore', f'--source={anterior}', '--staged', '--worktree', '--', *versionados)
        git(raiz, 'merge', '--ff-only', '--no-overwrite-ignore', destino)
        restaurar_configuracion(raiz, respaldo)
    except BaseException:
        if git(raiz, 'rev-parse', 'HEAD').stdout.strip() == anterior:
            # Incluye cambios preparados y no preparados, borrados y archivos nuevos.
            for relativo in (ALCANCE if preparado else movidos):
                retirar(raiz / relativo)
            for relativo in movidos:
                original = respaldo / relativo
                destino_local = raiz / relativo
                destino_local.parent.mkdir(parents=True, exist_ok=True)
                if original.is_symlink():
                    destino_local.symlink_to(os.readlink(original))
                elif original.is_dir():
                    shutil.copytree(original, destino_local, symlinks=True)
                else:
                    shutil.copy2(original, destino_local)
            shutil.copy2(respaldo / 'indice-git-original', indice)
            print('La actualización se detuvo; se restauraron los archivos y el índice originales.')
        else:
            print('Git avanzó, pero faltó completar la configuración local. Tu respaldo permanece en:', respaldo)
        raise
    print(f'Actualizado a {destino[:12]}. Las diez prácticas ya están en las carpetas de VS Code.')
    print('Tu configuración .env se conserva. Las copias anteriores están en el respaldo externo y en el historial de Git.')
    print('Para ejecutar: bash iniciar_practica_web.sh 1 (puedes elegir del 1 al 9).')
    print('Práctica 10: bash unidad-01-introduccion-ia/practicas/practica-10-agente-climatizacion/ejecutar.sh')
    return respaldo


def main():
    if len(sys.argv) > 2:
        print('Uso: python3 sincronizar_practicas.py [directorio_del_proyecto]', file=sys.stderr)
        return 2
    try:
        sincronizar(Path(sys.argv[1] if len(sys.argv) == 2 else '.').resolve())
    except (OSError, RuntimeError) as error:
        print(f'No se completó la actualización: {error}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Actualización interrumpida.', file=sys.stderr)
        return 130
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

