import gamestate

if __name__ == '__main__':
  """Here you can test the application using the shell."""
  try:
      player_a = gamestate.Player(1)
      player_b = gamestate.Player(2)
      board = gamestate.GameState()
      active_player = player_a
      while not board.is_full():
          board.printBoard()
          try:
              cell = int(input("Where do you want to place your sign? [1-9]"))
          except ValueError:
              continue
          cell = cell - 1
          if cell < 0 or cell > 8:
              print("Please enter a number between 1 and 9")
              continue
          if not board.turn(cell, active_player):
              print("Invalid Move")
              continue

          if board.checkForWin(active_player):
              print("You wonnered! GW.")
              exit(-1)

          if active_player == player_a:
              active_player = player_b
          else:
              active_player = player_a
      print('Tie')
    except KeyboardInterrupt:
      print('\nGoodbey!')
      exit(0)
