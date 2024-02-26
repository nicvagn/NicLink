
string toFen(unsigned char *data, size_t length) {
  if (length <= 32) {
    return "";
  }
  string fen = "";
  int empty = 0;
  for (int i = 0; i < 8; i++) {
    for (int j = 7; j >= 0; j--) {
      char piece =
          j % 2 == 0
              ? CHESS_PIECES[data[(i * 8 + j) / 2 + 2] & 0x0f]
              : CHESS_PIECES
                    [data[static_cast<int>(floor((i * 8 + j) / 2 + 2))] >> 4];
      if (piece == '0')
        empty++;
      else {
        if (empty > 0) {
          fen += to_string(empty);
          empty = 0;
        }
      }
      if (piece != '0')
        fen += piece;
    }
    if (empty > 0)
      fen += to_string(empty);
    if (i < 7)
      fen += "/";
    empty = 0;
  }
  return fen;
}
