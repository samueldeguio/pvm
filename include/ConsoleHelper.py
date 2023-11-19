class ConsoleHelper:
     
    """
    WIDE_OUTPUT_LENGTH:
        is the length of the output when using the wide option
    """
    WIDE_OUTPUT_LENGTH = 40
    
    def __init__(self, console):
        self.console = console

    def printError(self, text, wide : bool = False) -> None:
        """
        PrintError:
            Print error message to console

        Args:
            text (str): the error message to print
            wide (bool, optional): True if the message should be wide printed. Defaults to False.
        """

        style = "white on red"

        # if wide option is given style the error message
        if wide:
            text = " "+text.center(ConsoleHelper.WIDE_OUTPUT_LENGTH, " ")+" "
            text = " " * text.__len__() + "\n" + text + "\n" + " " * text.__len__()
            
        self.console.print(f"[{style}]{text}[/]")
