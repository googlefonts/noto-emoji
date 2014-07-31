/*
 * Copyright 2014 Google Inc. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Google contributors: Behdad Esfahbod, Roozbeh Pournader
 */

#include <cairo.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>


#define SCALE 8
#define SIZE 128
#define MARGIN (debug ? 24 : 0)

static unsigned int debug;

static cairo_path_t *wave_path_create(void) {
  cairo_surface_t *surface = cairo_image_surface_create(
      CAIRO_FORMAT_ARGB32, 0, 0);
  cairo_t *cr = cairo_create(surface);
  cairo_path_t *path;

  cairo_scale(cr, SCALE, SCALE);

  cairo_move_to(cr, 127.15, 81.52);
  cairo_rel_line_to(cr, -20.51, -66.94);
  cairo_rel_curve_to(cr, -0.61, -2, -2.22, -3.53, -4.25, -4.03);
  cairo_rel_curve_to(cr, -0.48, -0.12, -0.96, -0.18, -1.44, -0.18);
  cairo_rel_curve_to(cr, -1.56, 0, -3.07, 0.61, -4.2, 1.74);
  cairo_rel_curve_to(cr, -9.56, 9.56, -17.94, 11.38, -30.07, 11.38);
  cairo_rel_curve_to(cr, -3.68, 0, -7.72, -0.18, -11.99, -0.38);
  cairo_rel_curve_to(cr, -3.37, -0.15, -6.85, -0.31, -10.62, -0.4);
  cairo_rel_curve_to(cr, -0.66, -0.02, -1.31, -0.02, -1.95, -0.02);
  cairo_rel_curve_to(cr, -30.67, 0, -40.49, 18.56, -40.89, 19.35);
  cairo_rel_curve_to(cr, -0.52, 1.01, -0.73, 2.16, -0.62, 3.29);
  cairo_rel_line_to(cr, 6.72, 66.95);
  cairo_rel_curve_to(cr, 0.22, 2.22, 1.67, 4.13, 3.75, 4.95);
  cairo_rel_curve_to(cr, 0.7, 0.27, 1.43, 0.4, 2.16, 0.4);
  cairo_rel_curve_to(cr, 1.43, 0, 2.84, -0.52, 3.95, -1.5);
  cairo_rel_curve_to(cr, 0.1, -0.09, 12.42, -10.63, 32.13, -10.63);
  cairo_rel_curve_to(cr, 2.52, 0, 5.09, 0.17, 7.64, 0.51);
  cairo_rel_curve_to(cr, 9.27, 1.23, 16.03, 1.78, 21.95, 1.78);
  cairo_rel_curve_to(cr, 18.93, 0, 32.93, -6.1, 46.82, -20.38);
  cairo_curve_to(cr, 127.24, 85.85, 127.79, 83.59, 127.15, 81.52);
  cairo_close_path(cr);

  cairo_identity_matrix(cr);
  path = cairo_copy_path(cr);
  cairo_destroy(cr);
  cairo_surface_destroy(surface);

  return path;
}

static struct { double x, y; } mesh_points[] = {
  { -1,  43},
  { 30,  -3},
  { 77,  47},
  {104,   1},
  {130,  84},
  {100, 138},
  { 45,  80},
  {  7, 127},
};
#define M(i) mesh_points[i].x, mesh_points[i].y

static cairo_pattern_t *wave_mesh_create(void) {
  cairo_pattern_t *pattern = cairo_pattern_create_mesh();
  cairo_matrix_t scale_matrix = {1./SCALE, 0, 0, 1./SCALE, 0, 0};
  cairo_pattern_set_matrix(pattern, &scale_matrix);
  cairo_mesh_pattern_begin_patch(pattern);

  cairo_mesh_pattern_line_to(pattern,   M(0));
  cairo_mesh_pattern_curve_to(pattern,  M(1), M(2), M(3));
  cairo_mesh_pattern_line_to(pattern,   M(4));
  cairo_mesh_pattern_curve_to(pattern,  M(5), M(6), M(7));

  cairo_mesh_pattern_set_corner_color_rgb(pattern, 0, 0, 0, .5);
  cairo_mesh_pattern_set_corner_color_rgb(pattern, 1, 1, 0, .5);
  cairo_mesh_pattern_set_corner_color_rgb(pattern, 2, 1, 1, .5);
  cairo_mesh_pattern_set_corner_color_rgb(pattern, 3, 0, 1, .5);

  cairo_mesh_pattern_end_patch(pattern);

  return pattern;
}

static cairo_surface_t *scale_flag(cairo_surface_t *flag) {
  unsigned int w = cairo_image_surface_get_width(flag);
  unsigned int h = cairo_image_surface_get_height(flag);
  cairo_surface_t *scaled = cairo_image_surface_create(
      CAIRO_FORMAT_ARGB32, 256, 256);
  cairo_t *cr = cairo_create(scaled);

  cairo_scale(cr, 256./w, 256./h);

  cairo_set_source_surface(cr, flag, 0, 0);
  cairo_pattern_set_filter(cairo_get_source(cr), CAIRO_FILTER_BEST);
  cairo_pattern_set_extend(cairo_get_source(cr), CAIRO_EXTEND_PAD);
  cairo_paint(cr);

  cairo_destroy(cr);
  return scaled;
}

static cairo_surface_t *load_scaled_flag(const char *filename) {
  cairo_surface_t *flag = cairo_image_surface_create_from_png(filename);
  cairo_surface_t *scaled = scale_flag(flag);
  cairo_surface_destroy(flag);
  return scaled;
}

/* Returns 65536 for luminosoty of 1.0. */
static int luminosity(uint32_t pix) {
  unsigned int sr = (pix >> 16) & 0xFF;
  unsigned int sg = (pix >> 8) & 0xFF;
  unsigned int sb = pix & 0xFF;

  /* Apply gamma of 2.0 */
  sr = sr * sr;
  sg = sg * sg;
  sb = sb * sb;

  return  (sr * 13933u /* 0.2126 * 65536 */ +
     sg * 46871u /* 0.7152 * 65536 */ +
     sb *  4731u /* 0.0722 * 65536 */) / (255*255);
}

/* Returns luminosity. Only miningul if pixel is opaque.
 * If pixel is not opaque, sets *transparent to 1. */
static int luminosity_and_transparency(uint32_t pix, int *transparent) {
  if ((pix>>24) < 0xff) {
    *transparent = 1;
    return 0;
  }
  return luminosity(pix);
}

static double calculate_border_luminosity_and_transparency(
    cairo_surface_t *scaled_flag,
    int *transparent) {
  /* Some flags might have a border already.  As such, skip
   * a few pixels on each side... */
  const unsigned int skip = 5;
  uint32_t *s = (uint32_t *) cairo_image_surface_get_data(scaled_flag);
  unsigned int width  = cairo_image_surface_get_width(scaled_flag);
  unsigned int height = cairo_image_surface_get_height(scaled_flag);
  unsigned int sstride = cairo_image_surface_get_stride(scaled_flag) / 4;

  unsigned int luma = 0;
  unsigned int perimeter = (2 * ((width-2*skip) + (height-2*skip) - 2));

  assert(width > 2 * skip && height > 2 * skip);

  *transparent = 0;

  for (unsigned int x = skip; x < width - skip; x++)
    luma += luminosity_and_transparency(s[x], transparent);
  s += sstride;
  for (unsigned int y = 1 + skip; y < height - 1 - skip; y++) {
    luma += luminosity_and_transparency(s[skip], transparent);
    luma += luminosity_and_transparency(s[width - 1 - skip], transparent);
    s += sstride;
  }
  for (unsigned int x = skip; x < width - skip; x++)
    luma += luminosity_and_transparency(s[x], transparent);

  if (*transparent) {
    /* Flag is non-rectangular; eg. Nepal.
     * Don't draw a border. */
    return 0;
  }

  return luma / (65536. * perimeter);
}

static cairo_t *create_image(void) {
  cairo_surface_t *surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32,
                                                        (SIZE+2*MARGIN)*SCALE,
                                                        (SIZE+2*MARGIN)*SCALE);
  cairo_t *cr = cairo_create(surface);
  cairo_surface_destroy(surface);
  return cr;
}

static cairo_surface_t *wave_surface_create(void) {
  cairo_t *cr = create_image();
  cairo_surface_t *surface = cairo_surface_reference(cairo_get_target(cr));
  cairo_pattern_t *mesh = wave_mesh_create();
  cairo_set_source(cr, mesh);
  cairo_paint(cr);
  cairo_pattern_destroy(mesh);
  cairo_destroy(cr);
  return surface;
}

static cairo_surface_t *texture_map(cairo_surface_t *src,
                                    cairo_surface_t *tex) {
  uint32_t *s = (uint32_t *) cairo_image_surface_get_data(src);
  unsigned int width  = cairo_image_surface_get_width(src);
  unsigned int height = cairo_image_surface_get_height(src);
  unsigned int sstride = cairo_image_surface_get_stride(src) / 4;

  cairo_surface_t *dst = cairo_image_surface_create(CAIRO_FORMAT_ARGB32,
                                                    width, height);
  uint32_t *d = (uint32_t *) cairo_image_surface_get_data(dst);
  unsigned int dstride = cairo_image_surface_get_stride(dst) / 4;

  uint32_t *t = (uint32_t *) cairo_image_surface_get_data(tex);
  unsigned int twidth  = cairo_image_surface_get_width(tex);
  unsigned int theight = cairo_image_surface_get_height(tex);
  unsigned int tstride = cairo_image_surface_get_stride(tex) / 4;

  assert(twidth == 256 && theight == 256);

  for (unsigned int y = 0; y < height; y++) {
    for (unsigned int x = 0; x < width; x++) {
      unsigned int pix = s[x];
      unsigned int sa = pix >> 24;
      unsigned int sr = (pix >> 16) & 0xFF;
      unsigned int sg = (pix >> 8) & 0xFF;
      unsigned int sb = pix & 0xFF;
      if (sa == 0) {
        d[x] = 0;
        continue;
      }
      if (sa != 255) {
        sr = sr * 255 / sa;
        sg = sg * 255 / sa;
        sb = sb * 255 / sa;
      }
      assert(sb >= 127 && sb <= 129);
      d[x] = t[tstride * sg + sr];
    }
    s += sstride;
    d += dstride;
  }
  cairo_surface_mark_dirty(dst);

  return dst;
}

static void wave_flag(const char *filename, const char *out_prefix) {
  static cairo_path_t *wave_path;
  static cairo_surface_t *wave_surface;
  double border_luminosity;
  int border_transparent;
  char out[1000];

  cairo_surface_t *scaled_flag, *waved_flag;
  cairo_t *cr;

  if (!wave_path)
    wave_path = wave_path_create();
  if (!wave_surface)
    wave_surface = wave_surface_create();

  printf("Processing %s\n", filename);

  scaled_flag = load_scaled_flag(filename);
  border_luminosity = calculate_border_luminosity_and_transparency(
      scaled_flag,
      &border_transparent);
  waved_flag = texture_map(wave_surface, scaled_flag);
  cairo_surface_destroy(scaled_flag);

  cr = create_image();
  cairo_translate(cr, SCALE * MARGIN, SCALE * MARGIN);

  cairo_set_source_surface(cr, waved_flag, 0, 0);
  cairo_append_path(cr, wave_path);
  if (!debug)
    cairo_clip_preserve(cr);
  cairo_paint(cr);
  if (!border_transparent) {
    double border_alpha = .5 + fabs(.5 - border_luminosity);
    double border_width = 3 * SCALE;
    double border_gray = (1 - border_luminosity) * border_alpha;
    if (debug)
      printf("Border: alpha %g width %g gray %g\n",
             border_alpha, border_width/SCALE, border_gray);

    cairo_save(cr);
    cairo_set_source_rgba(cr,
                          border_gray, border_gray, border_gray, border_alpha);
    cairo_set_line_width(cr, border_width);
    if (!debug)
      cairo_set_operator(cr, CAIRO_OPERATOR_HSL_LUMINOSITY);
    cairo_stroke(cr);
    cairo_restore(cr);
  } else {
    printf("Transparent border\n");
    cairo_new_path(cr);
  }

  if (debug) {
    /* Draw mesh points. */
    cairo_save(cr);
    cairo_scale(cr, SCALE, SCALE);
    cairo_set_source_rgba(cr, .5, .0, .0, .9);
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
    for (unsigned int i = 0;
         i < sizeof(mesh_points) / sizeof(mesh_points[0]);
         i++) {
      cairo_move_to(cr, M(i));
      cairo_rel_line_to(cr, 0, 0);
    }
    cairo_set_line_width(cr, 2);
    cairo_stroke(cr);
    for (unsigned int i = 0; i < 4; i++) {
      cairo_move_to(cr, M(2*i));
      cairo_line_to(cr, M(2*i+1));
      cairo_move_to(cr, M(2*i));
      cairo_line_to(cr, M(7 - 2*i));
    }
    cairo_set_line_width(cr, .5);
    cairo_stroke(cr);
    cairo_restore(cr);
  }

  if (!debug) {
    /* Scale down, 2x at a time, to get best downscaling, because cairo's
     * downscaling is crap... :( */
    unsigned int scale = SCALE;
    while (scale > 1) {
      cairo_surface_t *old_surface, *new_surface;

      old_surface = cairo_surface_reference(cairo_get_target(cr));
      assert(scale % 2 == 0);
      scale /= 2;
      cairo_destroy(cr);
      new_surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32,
                                               (SIZE+2*MARGIN)*scale,
                                               (SIZE+2*MARGIN)*scale);
      cr = cairo_create(new_surface);
      cairo_scale(cr, .5, .5);
      cairo_set_source_surface(cr, old_surface, 0, 0);
      cairo_paint(cr);
      cairo_surface_destroy(old_surface);
      cairo_surface_destroy(new_surface);
    }
  }

  *out = '\0';
  strcat(out, out_prefix);
  strcat(out, filename);

  cairo_surface_write_to_png(cairo_get_target(cr), out);
  cairo_destroy(cr);
}

int main(int argc, char **argv) {
  const char *out_prefix;

  if (argc < 3) {
    fprintf(stderr, "Usage: [-debug] waveflag out-prefix [in.png]...\n");
    return 1;
  }

  if (!strcmp(argv[1], "-debug")) {
    debug = 1;
    argc--, argv++;
  }

  out_prefix = argv[1];
  argc--, argv++;

  for (argc--, argv++; argc; argc--, argv++)
    wave_flag(*argv, out_prefix);

  return 0;
}
