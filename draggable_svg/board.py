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


class Board:
    def __init__(
        self,
        svg_element,
        *,
        draggable=lambda element: "draggable" in element.classList,
        droppable=lambda element, target: True,
    ):
        """This makes the given svg_element to become a board (as in a board game).
        Every sub-element inside svg_element would become draggable and droppable.

        :param svg_element: The SVG tag you defined in your html file.
            A typical input can be ``document["id_of_the_svg_tag_in_my_html"]``
        :param callable draggable:
            A callback whose input would be the element being grabbed.
            It should return a boolean to determine whether a drag would be allowed.
            The default implementation allows everything with a class name as
            "draggable" to be draggable.
        :param callable droppable:
            A callback whose input would be the element being grabbed, and the target.
            It should return a boolean to determine whether a drop would be allowed.
            By default, you can drop at anywhere, including the backdrop.
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

        self.draggable = draggable
        self.droppable = droppable

    def _set_cursor(self, evt):
        target = evt.target
        if self.DragTarget:
            target.style.cursor = "grabbing" if self.droppable(
                self.DragTarget, target) else "not-allowed"
        else:
            target.style.cursor = (
                "grabbing"  # "grab" is not supported in Chrome
                if self.draggable(target) else "default")

    def _grab(self, evt):
        if evt.target == self.backdrop or not self.draggable(evt.target):
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

    def _move(self, x, y):
        assert self.DragTarget
        # apply a new tranform translation to the dragged element, to display
        # it in its new location
        self.DragTarget.setAttributeNS(None, "transform", f"translate({x},{y})")

    def _drag(self, evt):
        # account for zooming and panning
        self.TrueCoords.x, self.TrueCoords.y = self._get_true_coords(evt)
        if not self.DragTarget:
            # if we don't currently have an element in tow, don't do anything
            return
        self._move(
            # account for the offset between the element's origin and the exact
            # place we grabbed it... This way, the drag will look more natural
            self.TrueCoords.x - self.GrabPoint.x,
            self.TrueCoords.y - self.GrabPoint.y)

    def _drop(self, evt):
        if not self.DragTarget:
            # if we aren't currently dragging an element, don't do anything
            return
        if not self.droppable(self.DragTarget, evt.target):
            self._move(*self.drag_starting_differential)  # Revert to its before-drag position
                # We could also do self._move(0, 0) to revert to its original position
                # but that behavior is presumably unhelpful, so we don't do it here.
        self.DragTarget.setAttributeNS(
            # turn the pointer-events back on, so we can grab this item later
            None, "pointer-events", "all")
        self.DragTarget = None  # Otherwise, the dragged element sticks to the mouse
        evt.target.style.cursor = "default"

