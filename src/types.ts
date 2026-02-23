export type RgbColor = {
  r: number;
  g: number;
  b: number;
};

export type RgbaColor = RgbColor & {
  a: number;
};

export type PinPosition = {
  x: number;
  y: number;
};

export type ReplaceMode = 'all' | 'pin';
