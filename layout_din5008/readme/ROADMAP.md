- The `snailmail` module forces the paper format `base.paperformat_euro` when a
  letter is sent, unless the company paper format is `l10n_de.paperformat_euro_din`.
  Letters sent through snailmail with a DIN 5008 layout therefore use the
  standard margins.
- The side margins of a report come from the paper format; the layout expects
  0 mm side margins. Reports with their own paper format need a compatible one.
