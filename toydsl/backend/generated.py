class stencil:
    def __call__(self, in_field, out_field):
        for k in range(10):
            for i in range(1, 10):
                for j in range(10):
                    out_field[i, j, k] = in_field[i - 1, j, k]
