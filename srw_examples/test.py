# -*- coding: utf-8 -*-
"""
dot function test.
"""


def dot(A, B):
    """Function for multiplication of matrices.

    :param A: left matrix.
    :param B: right matrix.

    :return M: result of multiplication.
    """
    M = []
    for i in range(len(A[0])):
        M.append([])
        for j in range(len(B[0])):
            M[i].append(0.0)

    for i in range(len(A)):
        # Iterate through columns of B:
        for j in range(len(B[0])):
            # Iterate through rows of B:
            for k in range(len(B)):
                M[i][j] += A[i][k] * B[k][j]
    return M


if __name__ == '__main__':
    import numpy as np
    from uti_math import matr_prod

    a = [
        [12.1, 7, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    b = [
        [5, 8, 1, 2],
        [6, 7, 3, 0],
        [4, 5, 9, 1],
    ]

    m1 = dot(a, b)
    m2 = np.dot(a, b)
    m3 = matr_prod(a, b)

    print ''
