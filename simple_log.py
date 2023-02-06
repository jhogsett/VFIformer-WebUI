class SimpleLog:
    def __init__(self, verbose : bool):
        self.verbose = verbose
        self.messages = []
    
    def log(self, message : str) -> None:
        self.messages.append(message)
        if self.verbose:
            print(message)
