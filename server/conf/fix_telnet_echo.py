"""
Custom telnet protocol that properly handles ECHO negotiation, echoing, backspace, and cursor
"""
from evennia.server.portal.telnet import TelnetProtocol as BaseTelnetProtocol
from twisted.conch.telnet import ECHO, IAC, WILL

class TelnetProtocol(BaseTelnetProtocol):
    """
    Custom telnet protocol that ensures ECHO is properly negotiated and handled
    """
    
    def connectionMade(self):
        """
        Override to ensure ECHO is negotiated and cursor is visible
        """
        # Call the parent method first
        super().connectionMade()
        
        # Force the server to tell the client we WILL handle echo
        # This should make the client turn off local echo
        self.transport.write(IAC + WILL + ECHO)
        
        # Set a flag to enable echo
        self._echo_enabled = True
        
        # Track current line for backspace handling
        self._current_line = b""
        
        # Make cursor visible immediately
        self.transport.write(b'\x1b[?25h')  # Show cursor
        self.transport.write(b'\x1b[0m')    # Reset attributes
    
    def dataReceived(self, data):
        """
        Override dataReceived to echo back raw telnet data before processing
        """
        # Echo back characters with proper backspace and cursor handling
        if getattr(self, '_echo_enabled', False):
            for i, byte in enumerate(data):
                # Skip telnet IAC sequences (255 = IAC)
                if byte == 255:
                    continue
                    
                # Handle backspace (8 = BS, 127 = DEL)
                elif byte in [8, 127]:
                    if hasattr(self, '_current_line') and len(self._current_line) > 0:
                        # Remove last character from current line
                        self._current_line = self._current_line[:-1]
                        # Send backspace sequence: BS + space + BS
                        self.transport.write(b'\x08 \x08')
                
                # Handle carriage return/line feed
                elif byte in [10, 13]:  # LF or CR
                    self.transport.write(bytes([byte]))
                    self._current_line = b""
                
                # Handle printable characters
                elif byte >= 32 and byte <= 126:
                    self.transport.write(bytes([byte]))
                    if hasattr(self, '_current_line'):
                        self._current_line += bytes([byte])
                
                # Handle tab (expand to spaces for consistency)
                elif byte == 9:  # TAB
                    self.transport.write(b'    ')  # 4 spaces
                    if hasattr(self, '_current_line'):
                        self._current_line += b'    '
        
        # Call the parent method to handle telnet protocol
        super().dataReceived(data)
    
    def sendLine(self, line):
        """
        Override sendLine to ensure cursor is always visible after output
        """
        # Call parent method first
        result = super().sendLine(line)
        
        # After sending any line, make sure cursor is visible
        self.transport.write(b'\x1b[?25h')  # Show cursor
        
        return result
    
    def send_text(self, *args, **kwargs):
        """
        Override send_text to ensure cursor is visible after output
        """
        # Call parent method first
        result = super().send_text(*args, **kwargs)
        
        # Always ensure cursor is visible after any text output
        self.transport.write(b'\x1b[?25h')  # Show cursor
        
        return result
    
    def send_prompt(self, *args, **kwargs):
        """
        Override send_prompt to ensure cursor is visible after prompts
        """
        # Call parent method first
        result = super().send_prompt(*args, **kwargs)
        
        # Make sure cursor is visible for prompts
        self.transport.write(b'\x1b[?25h')  # Show cursor
        
        return result
