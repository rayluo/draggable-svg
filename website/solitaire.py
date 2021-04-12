from browser import document, svg, alert
import math
from draggable_svg import Board, show

ball_color = "sienna"
plate_color = "moccasin"

ray = 20
dx = dy = 60
left = 150
top = 160
filled = [
    [0,0,2,2,2,0,0],
    [0,2,2,2,2,2,0],
    [2,2,2,2,2,2,2],
    [2,2,2,1,2,2,2],
    [2,2,2,2,2,2,2],
    [0,2,2,2,2,2,0],
    [0,0,2,2,2,0,0]]

border_pos = - math.pi / 2 # angle for position of next place to put captured balls
store_ray = int(13.5 * ray)

# plate
center_x = left + 3 * dx
center_y = top  + 3 * dy

SVGRoot = document["board"]
SVGRoot.attach(svg.circle(  # big_plate
        cx=center_x,
        cy=center_y,
        r=15 * ray,
        style={"fill": plate_color, "stroke": ball_color}))
SVGRoot.attach(svg.circle(  # plate
        cx=center_x,
        cy=center_y,
        r=12 * ray,
        style={"fill": plate_color, "stroke": ball_color}))

for col in range(7):
    for row in range(7):
        if filled[col][row] >= 1:
            SVGRoot <= svg.circle(
                id = f"hole{row}_{col}",
                cx = left + col*dx,
                cy = top  + row*dy,
                r  = ray,
                style = {"fill": "white", "stroke":ball_color})
            if filled[col][row] == 2:
                ball = svg.circle(
                    id = f"ball{col}_{row}",
                    cx = left + col*dx,
                    cy = top  + row*dy,
                    r  = ray,
                    style = {"fill": ball_color})
                ball.classList.add("draggable")  # Brython can't create circle with class, so we do it afterwards
                SVGRoot <= ball
                filled[col][row] = ball
            else:
                filled[col][row] = None

def check_finished():
    # check if there are still possible moves
    remaining = 0
    for col in range(7):
        for row in range(7):
            if not filled[col][row]:
                continue
            remaining += 1
            if row >= 2 and filled[col][row - 1] and filled[col][row - 2] is None:
                return True # up
            if row <= 4 and filled[col][row + 1] and filled[col][row + 2] is None:
                return True # down
            if col >= 2 and filled[col - 1][row] and filled[col - 2][row] is None:
                return True # left
            if col <= 4 and filled[col + 1][row] and filled[col + 2][row] is None:
                return True # right
    if remaining == 1:
        alert("Congratulations, you win !")
    else:
        alert("Game over, %s balls remaining" %remaining)

def screenCoordsToGridCoords(x,y):
    return [int((x - left) / dx), int((y - top) / dy)]

class SolitaireBoard(Board):

    def _current_move(self, element, target):
        dx, dy = self.drag_starting_differential
        dragged_pos = screenCoordsToGridCoords(
            element.cx.baseVal.value + dx, element.cy.baseVal.value + dy)
        target_pos = screenCoordsToGridCoords(  # compute column and row of target
            target.cx.baseVal.value, int(target.attrs["cy"]))
        col_jumped_over = int((target_pos[0] + dragged_pos[0]) / 2)
        row_jumped_over = int((target_pos[1] + dragged_pos[1]) / 2)
        return dragged_pos, target_pos, col_jumped_over, row_jumped_over

    def droppable(self, element, target):
        if not target.id.startswith("hole"):
            return False
        dragged_pos, target_pos, col_jumped_over, row_jumped_over = self._current_move(
            element, target)
        newX = target_pos[0] - dragged_pos[0]
        newY = target_pos[1] - dragged_pos[1]
        return filled[col_jumped_over][row_jumped_over] and (
          newX == 0 and abs(newY) == 2 or newY == 0 and abs(newX)==2)

    def on_drop(self, element, target):
        # It will only be called when droppable() returns True
        global border_pos  # TODO: Can we avoid global?
        draggedBall = element
        dragged_pos, target_pos, col_jumped_over, row_jumped_over = self._current_move(
            draggedBall, target)

        # move this ball to the plate border
        removed = document[filled[col_jumped_over][row_jumped_over].id]
        cx = center_x + store_ray * math.cos(border_pos)
        cy = center_y + store_ray * math.sin(border_pos)
        show(removed, (cx - removed.cx.baseVal.value, cy - removed.cy.baseVal.value))
        removed.classList.remove("draggable")
        border_pos += math.pi / 18

        # reset dictionary
        filled[dragged_pos[0]][dragged_pos[1]] = None
        filled[col_jumped_over][row_jumped_over] = None
        filled[target_pos[0]][target_pos[1]] = draggedBall
        check_finished()

        # position dragged ball
        return (
            target.cx.baseVal.value - draggedBall.cx.baseVal.value,
            target.cy.baseVal.value - draggedBall.cy.baseVal.value)

SolitaireBoard(SVGRoot)

