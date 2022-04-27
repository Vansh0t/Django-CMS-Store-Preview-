
class Map(dict):
    def map(self, urls):
        def decorator(func):
                for url in urls:
                    self.update({url: func})
                return func
        return decorator
    def get_url(self, func):
        for key, value in self.items():
            #print(f'{value} ---- {func}')
            if value.__name__ == func.__name__:
                return key
        return None