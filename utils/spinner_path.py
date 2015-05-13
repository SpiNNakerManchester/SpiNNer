#!/usr/bin/env python

"""Print the path of the local SpiNNer installation."""

if __name__=="__main__":  # pragma: no cover
    import spinner
    import os.path
    print(os.path.dirname(spinner.__file__))
