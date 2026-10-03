"""Práctica 11: buscar rutas en un árbol binario mediante profundidad (DFS)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Nodo:
    valor: str
    izquierdo: Nodo | None = None
    derecho: Nodo | None = None


def construir_arbol() -> Nodo:
    """A tiene a B y C; B tiene a D; C tiene a E y F."""
    return Nodo(
        'A',
        izquierdo=Nodo('B', izquierdo=Nodo('D')),
        derecho=Nodo('C', izquierdo=Nodo('E'), derecho=Nodo('F')),
    )


def buscar_rutas(raiz: Nodo | None, destino: str | None = None) -> list[list[str]]:
    """Buscar todas las rutas al destino, o hasta las hojas si se omite el destino."""
    if destino is not None:
        if not isinstance(destino, str) or not destino.strip():
            raise ValueError('El destino debe ser el nombre de un nodo.')
        destino = destino.strip().upper()
    rutas = []

    def explorar(nodo: Nodo | None, camino: list[str]) -> None:
        if nodo is None:
            return
        ruta = camino + [nodo.valor]
        es_hoja = nodo.izquierdo is None and nodo.derecho is None
        if (destino is None and es_hoja) or nodo.valor == destino:
            rutas.append(ruta)
        # Se recorre primero la rama izquierda y después la derecha.
        explorar(nodo.izquierdo, ruta)
        explorar(nodo.derecho, ruta)

    explorar(raiz, [])
    return rutas


def mostrar_rutas(titulo: str, rutas: list[list[str]]) -> None:
    print(f'\n{titulo}')
    if not rutas:
        print('No se encontró ninguna ruta.')
        return
    for numero, ruta in enumerate(rutas, start=1):
        print(f'{numero}. {" -> ".join(ruta)}')
    print(f'Total de rutas: {len(rutas)}')


def main() -> None:
    arbol = construir_arbol()
    print('PRÁCTICA 11: RUTAS EN UN ÁRBOL BINARIO')
    print('Raíz: A')
    print('Rama izquierda: B, con hijo izquierdo D.')
    print('Rama derecha: C, con hijo izquierdo E e hijo derecho F.')
    mostrar_rutas('Todas las rutas desde A hasta una hoja:', buscar_rutas(arbol))
    mostrar_rutas('Rutas desde A hasta F:', buscar_rutas(arbol, 'F'))
    print('\nEn este árbol existe una sola ruta de A a F: A -> C -> F.')


if __name__ == '__main__':
    main()
