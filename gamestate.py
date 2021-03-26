class GameState:
  def __init__(self, player1, player2, channel):
    self.state = [0,0,0,0,0,0,0,0,0]
    self.player1 = player1
    self.player2 = player2
    self.active = player1
    self.channel = channel
  
  def turn(self, cell, player):
    if self.isValidTurn(cell):
      self.state[cell] = player.symbol
      return True
    else:
      return False
  
  def isValidTurn(self, cell):
    return self.state[cell] == 0

  def checkForWin(self, player):
    s = player.symbol
    if self.state[0] == s and self.state[1] == s and self.state[2] == s:
        return True
    elif self.state[3] == s and self.state[4] == s and self.state[5] == s:
        return True
    elif self.state[6] == s and self.state[7] == s and self.state[8] == s:
        return True

    elif self.state[0] == s and self.state[3] == s and self.state[6] == s:
        return True
    elif self.state[1] == s and self.state[4] == s and self.state[7] == s:
        return True
    elif self.state[2] == s and self.state[5] == s and self.state[8] == s:
        return True

    elif self.state[0] == s and self.state[4] == s and self.state[8] == s:
        return True
    elif self.state[2] == s and self.state[4] == s and self.state[6] == s:
        return True


  def sign_to_emoji(self, sign):
    if sign == 0:
      return ":black_large_square:"
    elif sign == 1:
      return ":white_circle:"
    else:
      return ":red_circle:"
    
  def getBoardForMessageAsList(self):
    list = []
    row1 = self.sign_to_emoji(self.state[0]) + self.sign_to_emoji(self.state[1]) + self.sign_to_emoji(self.state[2])
    list.append(row1)
    row2 = self.sign_to_emoji(self.state[3]) + self.sign_to_emoji(self.state[4]) + self.sign_to_emoji(self.state[5])
    list.append(row2)
    row3 = self.sign_to_emoji(self.state[6]) + self.sign_to_emoji(self.state[7]) + self.sign_to_emoji(self.state[8])
    list.append(row3)
    return list

  def printBoard(self):
    for line in self.getBoardForMessageAsList():
      print(line)

class Player:
  def __init__(self, symbol, name, discriminator):
    self.symbol = symbol
    self.name = name
    self.discriminator = discriminator


class DiscordGameState:
  def __init__(self, user1, user2):
    self.user_a = user1
    self.user_b = user2
    self.player_a = Player(1)
    self.player_b = Player(2)
    self.activePlayer = self.player_a
    self.mapping = {
      self.user_a: self.player_a,
      self.user_b: self.player_b,
      self.player_a: self.user_a,
      self.player_b: self.user_b
    }

  def playerToUser(self, user):
    player = self.mapping.get(user)
    if not player:
      return False
    else:
      return player

  def userToPlayer(self, player):
    user = self.mapping.get(player)
    if not user:
      return False
    else:
      return user

    def processMessage(self, user, message):
      if self.activePlayer != self.playerToUser(user):
        return False
