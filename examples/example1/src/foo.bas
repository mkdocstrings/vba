Attribute VB_Name = "foo"
' This is the file docstring.
' Like all other, it can be multiple lines
'
' Examples:
'
'     >>> foo(bar)
'     baz

Option Explicit
Option Compare Text

Function fuzz_HotelEcho_helper( _
            WS As Worksheet, _
            Name As String, _
            description As String) As listObject 'This comment is not part of the docs.
    ' This is a docstring.
    '
    ' Arguments:
    '     WS: The worksheet
    '     Name: The name
    '     description: The description
    '
    ' Returns:
    '     A fancy ListObject
    '
    ' Examples:
    '     >>> fuzz_HotelEcho_helper(sheet, "foo", "the sheet")
    '     ListObject(...)

    ' This comment is not part of the docs.
    If moo Then
        milk the cow
    End If

End Function

Sub asdf123QwerZxcv_yuio(fooBar As listObject)
    ' This is another docstring.

    doSomething
End Sub

Public Sub dolf()
    ' sub docstring
End Sub

Public Property Get asdf() As Variant
    ' property get docstring
End Property

Public Property Let asdf(ByVal vNewValue As Variant)
    ' property let docstring
End Property
