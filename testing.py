from openbci_stream.acquisition import Cyton

cyton = Cyton("serial", "COM3")
cyton.start_streaming()