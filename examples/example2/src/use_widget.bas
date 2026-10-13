' Uses [Widget][] and its [reset][] procedure.

Public Function makeWidget(value As Widget, items As Variant, missing As MissingType, Optional label As String = "Widget") As Widget
    ' Build a [Widget][].
    '
    ' Args:
    '     VALUE: The input widget.
    '     ITEMS (list[Widget]): The input widgets.
    '     missing (MissingType): An external type without a documentation target.
    '     LABEL: A label that stays a literal default value.
    '
    ' Returns:
    '     The resulting widget.
End Function

Public Function chooseValue(value, Optional fallback = 2)
    ' Choose a value.
    '
    ' Args:
    '     VALUE: The preferred value.
    '     fallback: The fallback value.
    '
    ' Returns:
    '     The selected value.
    chooseValue = value
End Function

Public Property Get currentValue()
    ' Read the current value.
    '
    ' Returns:
    '     The current value.
    currentValue = 2
End Property
