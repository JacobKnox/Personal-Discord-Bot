class GeneralException(Exception):
  def __init__(self, exception: Exception) -> None:
    super().__init__()
    self.name = exception.__class__.__name__
    self.message = ', '.join(exception.args)

class NoNationFoundException(Exception):
  def __init__(self, id: int) -> None:
    super().__init__()
    self.name = "NoNationFoundException"
    self.message = f"No nation exists with nation {id}."
    
class InvalidResourceException(Exception):
  def __init__(self, resource: str) -> None:
    super().__init__()
    self.name = "InvalidResourceException"
    self.message = f"{resource.capitalize()} is not a valid resource."