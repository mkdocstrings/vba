Attribute VB_Name = "ArraySummary"
' Summarize numeric values in a one-dimensional array.
' Use [SumNumbers][] for a total and [CountNumbers][] for the number of numeric entries.

Option Explicit

Public Function SumNumbers(ByVal values As Variant) As Double
    ' Add the numeric entries in an array.
    '
    ' Args:
    '     values: A one-dimensional array, such as Array(12, Empty, "pending", 8).
    '         Strings, Boolean values, blanks, and errors are ignored.
    '
    ' Returns:
    '     The sum of the numeric entries, or zero if none are present.
    '
    ' Examples:
    '     ```vb
    '     Debug.Print SumNumbers(Array(12, Empty, "pending", 8))  ' 20
    '     ```
    '
    ' See also [CountNumbers][] for the number of numeric entries.
    Dim item As Variant
    For Each item In values
        Select Case VarType(item)
            Case vbByte, vbInteger, vbLong, vbSingle, vbDouble, vbCurrency, vbDecimal
                SumNumbers = SumNumbers + CDbl(item)
#If Win64 Then
            Case vbLongLong
                SumNumbers = SumNumbers + CDbl(item)
#End If
        End Select
    Next item
End Function

Public Function CountNumbers(ByVal values As Variant) As Long
    ' Count the numeric entries in an array.
    '
    ' Args:
    '     values: A one-dimensional array. Strings, Boolean values, blanks, and errors are ignored.
    '
    ' Returns:
    '     The number of numeric entries, or zero if none are present.
    '
    ' Examples:
    '     ```vb
    '     Debug.Print CountNumbers(Array(12, Empty, "pending", 8))  ' 2
    '     ```
    '
    ' See also [SumNumbers][] for the total of the numeric entries.
    Dim item As Variant
    For Each item In values
        Select Case VarType(item)
            Case vbByte, vbInteger, vbLong, vbSingle, vbDouble, vbCurrency, vbDecimal
                CountNumbers = CountNumbers + 1
#If Win64 Then
            Case vbLongLong
                CountNumbers = CountNumbers + 1
#End If
        End Select
    Next item
End Function
