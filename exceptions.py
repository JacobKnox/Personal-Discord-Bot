class GeneralException(RuntimeError):
  def __init__(self, exception):
    super().__init__()
    self.name = exception.__class__.__name__
    self.message = exception.args

class NoNationFoundException(RuntimeError):
  def __init__(self, message):
    super().__init__()
    self.name = "NoNationFoundException"
    self.message = message