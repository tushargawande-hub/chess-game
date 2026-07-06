import pygame

pygame.init()
SIZE = 400
screen = pygame.display.set_mode((SIZE, SIZE))

# Game state
board = [['' for _ in range(3)] for _ in range(3)]
turn = 'X'
winner = None
cell = SIZE // 3


def draw_board():
    screen.fill((240, 240, 240))

    # Grid lines
    for i in range(1, 3):
        pygame.draw.line(screen, (60, 60, 60), (i * cell, 20), (i * cell, SIZE - 20), 3)
        pygame.draw.line(screen, (60, 60, 60), (20, i * cell), (SIZE - 20, i * cell), 3)

    # Draw X and O
    for r in range(3):
        for c in range(3):
            cx = c * cell + cell // 2
            cy = r * cell + cell // 2
            if board[r][c] == 'X':
                offset = cell // 3
                pygame.draw.line(screen, (220, 50, 50), (cx - offset, cy - offset), (cx + offset, cy + offset), 5)
                pygame.draw.line(screen, (220, 50, 50), (cx + offset, cy - offset), (cx - offset, cy + offset), 5)
            elif board[r][c] == 'O':
                pygame.draw.circle(screen, (50, 50, 220), (cx, cy), cell // 3, 4)

    # Status text
    font = pygame.font.Font(None, 32)
    if winner:
        if winner == 'draw':
            text = font.render("It's a draw!", True, (100, 100, 100))
        else:
            text = font.render(f'{winner} wins!', True, (0, 150, 0))
    else:
        text = font.render(f"{turn}'s turn", True, (80, 80, 80))
    r = text.get_rect(center=(SIZE // 2, SIZE - 15))
    screen.blit(text, r)

    pygame.display.flip()


def check_winner():
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != '':
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != '':
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] != '':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != '':
        return board[0][2]
    if all(board[r][c] != '' for r in range(3) for c in range(3)):
        return 'draw'
    return None


draw_board()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if winner:
                # Restart
                board = [['' for _ in range(3)] for _ in range(3)]
                turn = 'X'
                winner = None
            else:
                mx, my = event.pos
                col = mx // cell
                row = my // cell
                if 0 <= row < 3 and 0 <= col < 3 and board[row][col] == '':
                    board[row][col] = turn
                    winner = check_winner()
                    turn = 'O' if turn == 'X' else 'X'
            draw_board()

    pygame.time.wait(50)

pygame.quit()