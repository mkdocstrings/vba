' Document procedures with their original source.

Private Const offset As Long = 1 + _
    2

  Public Function chooseValue( _
      value As Long, _
      Optional fallback As Long = 2) As Long
      ' Choose a value.
      '
      ' Args:
      '     value: The preferred value.
      '     fallback: The fallback value.
      '
      ' Returns:
      '     The selected value.
      If value > 0 Then
          chooseValue = value + _
              offset
      Else
          chooseValue = fallback
      End If
  End Function ' Finished choosing.

Public Sub later(value)
    ' Use a value after the continued statements.
    '
    ' Args:
    '     value: The input value.
    value = 2 ' This underscore is comment text: _
End Sub
