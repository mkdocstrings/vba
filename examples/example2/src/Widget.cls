Attribute VB_Name = "Widget"
' A documented widget.

Public Sub reset()
    ' Reset the widget.
End Sub

Public Property Get item(key As Variant) As Variant
    ' Read an item.
    '
    ' Args:
    '     key: The item key.
    '
    ' Returns:
    '     The selected item.
End Property

Public Property Let item(key As Variant, value As Variant)
    ' Store a value.
    '
    ' Args:
    '     key: The item key.
    '     value: The new value.
End Property

Public Property Set item(key As Variant, value As Variant)
    ' Store an object.
    '
    ' Args:
    '     key: The item key.
    '     value: The new object.
End Property
