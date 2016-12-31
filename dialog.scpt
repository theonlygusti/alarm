on run argv
  tell application "System Events" to display dialog (item 1 of argv) buttons { "Ok" } default button "Ok" with icon file (path of container of (path to me) & "Icon.png")
end run
