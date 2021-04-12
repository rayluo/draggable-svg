__version__ = "0.1.0"

# Drag API does not work on SVG. https://www.w3.org/TR/SVG/svgdom.html#RelationshipWithDOM2Events
# This module uses mousedown, mousemove and mouseup to simulate drag and drop,
# inspired by Doug Schepers's module at http://svg-whiz.com/svg/DragAndDrop.svg

# Note: Another useful learning source
# https://www.petercollingridge.co.uk/tutorials/svg/interactive/dragging/


def get_differential(element):
    """Return the differential as (x,y) between element's current on-screen spot
    and its real spot.
    """
    transMatrix = element.getCTM()
    return transMatrix.e, transMatrix.f


def show(element, differential):
    """Show element at differential (x, y) spot of its real position.

    The element's real coordinate (x, y) is *not* changed by this function.
    """
    x, y = differential
    element.setAttributeNS(None, "transform", f"translate({x},{y})")


class Board:
    def __init__(
        self,
        svg_element,
        *,
        draggable=None,
        droppable=None,
        on_drop=None,
    ):
        """This makes the given svg_element to become a board (as in a board game).
        Every sub-element inside svg_element would become draggable and droppable.

        :param svg_element: The SVG tag you defined in your html file.
            A typical input can be ``document["id_of_the_svg_tag_in_my_html"]``

        :param callable draggable: An alternative way to customize self.draggable()
        :param callable droppable: An alternative way to customize self.droppable()
        :param callable on_drop: An alternative way to customize self.on_drop()
        """
        backdrops = svg_element.select("#BackDrop")
        if not backdrops:  # Then automatically create one as first child
            from browser import svg  # Requires to be run inside Brython environment
            backdrop_element = svg.rect(
                id="BackDrop", x="-10%", y="-10%", width="110%", height="110%",
                fill="none", pointer_events="all")
            svg_element.insertBefore(backdrop_element, svg_element.firstChild)
        else:
            backdrop_element = backdrops[0]

        # this will serve as the canvas over which items are dragged.
        # having the drag events occur on the mousemove over a backdrop
        # (instead of the dragged element) prevents the dragged element
        # from being inadvertantly dropped when the mouse is moved rapidly
        self.backdrop = backdrop_element

        self.svg_root = svg_element
        # these svg points hold x and y values...
        # very handy, but they do not display on the screen (just so you know)
        self.TrueCoords = self.svg_root.createSVGPoint()
        self.GrabPoint = self.svg_root.createSVGPoint()

        self.DragTarget = None  # It will store the element being dragged
        self.drag_starting_differential = (0, 0)  # Placeholder for an (x,y) differential

        self.svg_root.bind("mousedown", self._grab)
        self.svg_root.bind("mousemove", self._drag)
        self.svg_root.bind("mouseup", self._drop)
        self.svg_root.bind(
            "mousemove",  # mouseover fires only once when entering a new shape
            self._set_cursor)

        self._draggable = draggable or self.draggable
        self._droppable = droppable or self.droppable
        self._on_drop = on_drop or self.on_drop

    def draggable(self, element):
        """
        Return a boolean to determine whether a drag on element would be allowed.

        By default, element with "draggable" class name is draggable.
        """
        return "draggable" in element.classList

    def droppable(self, element, target):
        """Return a boolean to determine whether element can be dropped on target.

        The default implementation allows a drop on anywhere.
        """
        return True

    def on_drop(self, element, target):
        """The callback function to perform your customized after-drop operations.

        It will be called when user releases the dragging element onto target,
        AND when the corresponding ``droppable(element, target)`` returns True.

        :returns:
            Either ``None`` to mean the element is dropped as-is,
            or an (x, y) differential to "snap" the element into
            a customized location (original_x + x, original_y + y).
            The default implementation returns a None.
        """
        return None

    def _set_cursor(self, evt):
        target = evt.target
        if self.DragTarget:
            target.style.cursor = "grabbing" if self._droppable(
                self.DragTarget, target) else "not-allowed"
        else:
            target.style.cursor = (
                "grabbing"  # "grab" is not supported in Chrome
                if self._draggable(target) else "default")

    def _grab(self, evt):
        if evt.target == self.backdrop or not self._draggable(evt.target):
            # you cannot drag the background itself,
            # so ignore any attempts to mouse down on it
            return

        self.DragTarget = evt.target  # TODO: Grab a Group: .parentNode

        # move this element to the "top" of the display, so it is (almost)
        # always over other elements
        self.DragTarget.parentNode.appendChild(self.DragTarget)

        # turn off all pointer events to the dragged element, this does 2 things:
        #    1) allows us to drag text elements without selecting the text
        #    2) allows us to find out where the dragged element is dropped (see Drop)
        self.DragTarget.setAttributeNS(None, "pointer-events", "none")

        # we need to find the current position and translation of the grabbed element,
        # so that we only apply the differential between the current location
        # and the new location
        dx, dy = self.drag_starting_differential = get_differential(self.DragTarget)
        self.GrabPoint.x = self.TrueCoords.x - dx
        self.GrabPoint.y = self.TrueCoords.y - dy

    def _get_true_coords(self, evt):
        # find the current zoom level and pan setting, and adjust the reported
        # mouse position accordingly
        newScale = self.svg_root.currentScale
        translation = self.svg_root.currentTranslate
        x = (evt.clientX - translation.x) / newScale
        y = (evt.clientY - translation.y) / newScale
        return (x, y)

    def _drag(self, evt):
        # account for zooming and panning
        self.TrueCoords.x, self.TrueCoords.y = self._get_true_coords(evt)
        if not self.DragTarget:
            # if we don't currently have an element in tow, don't do anything
            return
        show(self.DragTarget, (
            # account for the offset between the element's origin and the exact
            # place we grabbed it... This way, the drag will look more natural
            self.TrueCoords.x - self.GrabPoint.x,
            self.TrueCoords.y - self.GrabPoint.y))

    def _drop(self, evt):
        if not self.DragTarget:
            # if we aren't currently dragging an element, don't do anything
            return
        if not self._droppable(self.DragTarget, evt.target):
            revert_to = (
                # We could use (0, 0) to revert to its original position
                # but that behavior is presumably unhelpful, so we don't do it here.
                self.drag_starting_differential)
            show(self.DragTarget, revert_to)  # Revert to its before-drag position
        else:
            new_differential = self._on_drop(self.DragTarget, evt.target)
            if new_differential:
                show(self.DragTarget, new_differential)
        self.DragTarget.setAttributeNS(
            # turn the pointer-events back on, so we can grab this item later
            None, "pointer-events", "all")
        self.DragTarget = None  # Otherwise, the dragged element sticks to the mouse
        evt.target.style.cursor = "default"

