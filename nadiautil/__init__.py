import pathlib

def getIntervals(path):

    intervals = 0

    path = pathlib.Path(path)    
    for x in [x for x in path.iterdir() if x.is_dir()]:
        with open(x.joinpath('intervals')) as f:
            intervals = intervals + len([str(line).strip() for line in f])

    return intervals



