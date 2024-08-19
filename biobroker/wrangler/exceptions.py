class NoResults(Exception):
    def __init__(self):
        super().__init__("No results to write")