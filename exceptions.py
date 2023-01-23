class GeneralException(Exception):
  "A general exception class."
  
  def __init__(self, exception: Exception) -> None:
    self.name = exception.__class__.__name__
    self.message = ', '.join(exception.args)
    super().__init__(super().__init__(self.message))
  
  pass

class NoNationFoundException(Exception):
  """Exception raised when no nation is found with a given id number.

    Attributes:
        id -- id number which caused the error
    """
  
  def __init__(self, id: int) -> None:
    self.name = "NoNationFoundException"
    self.message = f"No nation exists with nation {id}."
    super().__init__(self.message)
  
  pass
    
class InvalidResourceException(Exception):
  """Exception raised when a resource does not exist in the game.

    Attributes:
        resource -- resource which caused the error
    """
  
  def __init__(self, resource: str) -> None:
    self.name = "InvalidResourceException"
    self.message = f"{resource.capitalize()} is not a valid resource."
    super().__init__(self.message)
  
  pass
    
class NoTokenException(Exception):
  "Exception raised when no Discord token is provided."
  
  def __init__(self) -> None:
    self.name = "NoTokenException"
    self.message = "No Discord token has been provided. The bot cannot run."
    super().__init__(self.message)
  
  pass

class NoKeyException(Exception):
  "Exception raised when no API key is provided."
  
  def __init__(self, key_name) -> None:
    self.name = "NoKeyException"
    self.message = f"{key_name} has not been provided. Functions relying on it will not work."
    super().__init__(self.message)
  
  pass