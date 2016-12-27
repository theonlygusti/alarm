on run argv
  tell application "System Events" to display dialog (item 1 of argv) with icon file (path of container of (path to me) & "Icon.png")
end run
