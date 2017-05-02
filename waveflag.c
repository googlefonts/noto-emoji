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
 * Google contributors: Behdad Esfahbod
 */

#include <cairo.h>
#include <libgen.h> // basename
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>


#define SCALE 8
#define SIZE 128
#define MARGIN (debug ? 4 : 0)

static unsigned int debug;

#define std_aspect (5./3.)
#define top 21
#define bot 128-top
#define B 21
#define C 4
static struct { double x, y; } mesh_points[] =
{
  {  1, top+C},
  { 43, top-B+C},
  { 85, top+B-C},
  {127, top-C},
  {127, bot-C},
  { 85, bot+B-C},
  { 43, bot-B+C},
  {  1, bot+C},
};
#define M(i) \
	x_aspect (mesh_points[i].x, aspect), \
	y_aspect (mesh_points[i].y, aspect)

static inline double x_aspect (double v, double aspect)
{
	return aspect >= 1. ? v : (v - 64) * aspect + 64;
}
static inline double y_aspect (double v, double aspect)
{
	return aspect <= 1. ? v : (v - 64) / aspect + 64;
}

static cairo_path_t *
wave_path_create (double aspect)
{
	cairo_surface_t *surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32, 0,0);
	cairo_t *cr = cairo_create (surface);
	cairo_path_t *path;

	cairo_scale (cr, SIZE/128.*SCALE, SIZE/128.*SCALE);

	cairo_line_to(cr,   M(0));
	cairo_curve_to(cr,  M(1), M(2), M(3));
	cairo_line_to(cr,   M(4));
	cairo_curve_to(cr,  M(5), M(6), M(7));
	cairo_close_path (cr);

	cairo_identity_matrix (cr);
	path = cairo_copy_path (cr);
	cairo_destroy (cr);
	cairo_surface_destroy (surface);

	return path;
}

static cairo_pattern_t *
wave_mesh_create (double aspect, int alpha)
{
	cairo_pattern_t *pattern = cairo_pattern_create_mesh();
	cairo_matrix_t scale_matrix = {128./SIZE/SCALE, 0, 0, 128./SIZE/SCALE, 0, 0};
	cairo_pattern_set_matrix (pattern, &scale_matrix);
	cairo_mesh_pattern_begin_patch(pattern);

	cairo_mesh_pattern_line_to(pattern,   M(0));
	cairo_mesh_pattern_curve_to(pattern,  M(1), M(2), M(3));
	cairo_mesh_pattern_line_to(pattern,   M(4));
	cairo_mesh_pattern_curve_to(pattern,  M(5), M(6), M(7));

	if (alpha)
	{
		cairo_mesh_pattern_set_corner_color_rgba(pattern, 0, 1, 1, 1, .5);
		cairo_mesh_pattern_set_corner_color_rgba(pattern, 1,.5,.5,.5, .5);
		cairo_mesh_pattern_set_corner_color_rgba(pattern, 2, 0, 0, 0, .5);
		cairo_mesh_pattern_set_corner_color_rgba(pattern, 3,.5,.5,.5, .5);
	}
	else
	{
		cairo_mesh_pattern_set_corner_color_rgb(pattern, 0, 0, 0, .5);
		cairo_mesh_pattern_set_corner_color_rgb(pattern, 1, 1, 0, .5);
		cairo_mesh_pattern_set_corner_color_rgb(pattern, 2, 1, 1, .5);
		cairo_mesh_pattern_set_corner_color_rgb(pattern, 3, 0, 1, .5);
	}

	cairo_mesh_pattern_end_patch(pattern);

	return pattern;
}

static cairo_surface_t *
scale_flag (cairo_surface_t *flag)
{
	unsigned int w = cairo_image_surface_get_width  (flag);
	unsigned int h = cairo_image_surface_get_height (flag);
	cairo_surface_t *scaled = cairo_image_surface_create (CAIRO_FORMAT_ARGB32, 256,256);
	cairo_t *cr = cairo_create (scaled);

	cairo_scale (cr, 256./w, 256./h);

	cairo_set_source_surface (cr, flag, 0, 0);
	cairo_pattern_set_filter (cairo_get_source (cr), CAIRO_FILTER_BEST);
	cairo_pattern_set_extend (cairo_get_source (cr), CAIRO_EXTEND_PAD);
	cairo_paint (cr);

	cairo_destroy (cr);
	return scaled;
}

static cairo_surface_t *
load_scaled_flag (const char *filename, double *aspect)
{
	cairo_surface_t *flag = cairo_image_surface_create_from_png (filename);
	cairo_surface_t *scaled = scale_flag (flag);
	*aspect = (double) cairo_image_surface_get_width (flag) /
		  (double) cairo_image_surface_get_height (flag);
	cairo_surface_destroy (flag);
	return scaled;
}

static int
is_transparent (uint32_t pix)
{
	return ((pix>>24) < 0xff);
}

static int
border_is_transparent (cairo_surface_t *scaled_flag)
{
	/* Some flags might have a border already.  As such, skip
	 * a few pixels on each side... */
	const unsigned int skip = 5;
	uint32_t *s = (uint32_t *) cairo_image_surface_get_data (scaled_flag);
	unsigned int width  = cairo_image_surface_get_width (scaled_flag);
	unsigned int height = cairo_image_surface_get_height (scaled_flag);
	unsigned int sstride = cairo_image_surface_get_stride (scaled_flag) / 4;

	int transparent = 0;

	assert (width > 2 * skip && height > 2 * skip);


	for (unsigned int x = skip; x < width - skip; x++)
		transparent |= is_transparent (s[x]);
	s += sstride;
	for (unsigned int y = 1 + skip; y < height - 1 - skip; y++)
	{
		transparent |= is_transparent (s[skip]);
		transparent |= is_transparent (s[width - 1 - skip]);
		s += sstride;
	}
	for (unsigned int x = skip; x < width - skip; x++)
		transparent |= is_transparent (s[x]);

	return transparent;
}

static cairo_t *
create_image (void)
{
	cairo_surface_t *surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
							       (SIZE+2*MARGIN)*SCALE,
							       (SIZE+2*MARGIN)*SCALE);
	cairo_t *cr = cairo_create (surface);
	cairo_surface_destroy (surface);
	return cr;
}

static cairo_surface_t *
wave_surface_create (double aspect)
{
	cairo_t *cr = create_image ();
	cairo_surface_t *surface = cairo_surface_reference (cairo_get_target (cr));
	cairo_pattern_t *mesh = wave_mesh_create (aspect, 0);
	cairo_set_source (cr, mesh);
	cairo_paint (cr);
	cairo_pattern_destroy (mesh);
	cairo_destroy (cr);
	return surface;
}

static cairo_surface_t *
texture_map (cairo_surface_t *src, cairo_surface_t *tex)
{
	uint32_t *s = (uint32_t *) cairo_image_surface_get_data (src);
	unsigned int width  = cairo_image_surface_get_width (src);
	unsigned int height = cairo_image_surface_get_height (src);
	unsigned int sstride = cairo_image_surface_get_stride (src) / 4;

	cairo_surface_t *dst = cairo_image_surface_create (CAIRO_FORMAT_ARGB32, width, height);
	uint32_t *d = (uint32_t *) cairo_image_surface_get_data (dst);
	unsigned int dstride = cairo_image_surface_get_stride (dst) / 4;

	uint32_t *t = (uint32_t *) cairo_image_surface_get_data (tex);
	unsigned int twidth  = cairo_image_surface_get_width (tex);
	unsigned int theight = cairo_image_surface_get_height (tex);
	unsigned int tstride = cairo_image_surface_get_stride (tex) / 4;

	assert (twidth == 256 && theight == 256);

	for (unsigned int y = 0; y < height; y++)
	{
		for (unsigned int x = 0; x < width; x++)
		{
			unsigned int pix = s[x];
			unsigned int sa = pix >> 24;
			unsigned int sr = (pix >> 16) & 0xFF;
			unsigned int sg = (pix >>  8) & 0xFF;
			unsigned int sb = (pix      ) & 0xFF;
			if (sa == 0)
			{
				d[x] = 0;
				continue;
			}
			if (sa != 255)
			{
				sr = sr * 255 / sa;
				sg = sg * 255 / sa;
				sb = sb * 255 / sa;
			}
			assert (sb >= 127 && sb <= 129);
			d[x] = t[tstride * sg + sr];
		}
		s += sstride;
		d += dstride;
	}
	cairo_surface_mark_dirty (dst);

	return dst;
}

static void
wave_flag (const char *filename, const char *out_prefix)
{
	static cairo_path_t *standard_wave_path;
	static cairo_surface_t *standard_wave_surface;
	cairo_path_t *wave_path;
	cairo_surface_t *wave_surface;
	int border_transparent;
	char out[1000];
	double aspect = 0;

	cairo_surface_t *scaled_flag, *waved_flag;
	cairo_t *cr;

	if (debug) printf ("Processing %s\n", filename);

	scaled_flag = load_scaled_flag (filename, &aspect);

	aspect /= std_aspect;
	aspect = sqrt (aspect); // Discount the effect
	if (.9 <= aspect && aspect <= 1.1)
	{
		if (debug) printf ("Standard aspect ratio\n");
		aspect = 1.;
	}

	if (aspect == 1.)
	{
		if (!standard_wave_path)
			standard_wave_path = wave_path_create (aspect);
		if (!standard_wave_surface)
			standard_wave_surface = wave_surface_create (aspect);
		wave_path = standard_wave_path;
		wave_surface = standard_wave_surface;
	}
	else
	{
		wave_path = wave_path_create (aspect);
		wave_surface = wave_surface_create (aspect);
	}


	border_transparent = border_is_transparent (scaled_flag);
	waved_flag = texture_map (wave_surface, scaled_flag);
	cairo_surface_destroy (scaled_flag);

	cr = create_image ();
	cairo_translate (cr, SCALE * MARGIN, SCALE * MARGIN);

	// Paint waved flag
	cairo_set_source_surface (cr, waved_flag, 0, 0);
	cairo_append_path (cr, wave_path);
	if (!debug)
		cairo_clip_preserve (cr);
	cairo_paint (cr);

	// Paint border
	if (!border_transparent)
	{
		double border_alpha = .2;
		double border_width = 4 * SCALE;
		double border_gray = 0x42/255.;
		if (debug)
			printf ("Border: alpha %g width %g gray %g\n",
				border_alpha, border_width/SCALE, border_gray);

		cairo_save (cr);
		cairo_set_source_rgba (cr,
				       border_gray * border_alpha,
				       border_gray * border_alpha,
				       border_gray * border_alpha,
				       border_alpha);
		cairo_set_line_width (cr, 2*border_width);
		if (!debug)
			cairo_set_operator (cr, CAIRO_OPERATOR_MULTIPLY);
		cairo_stroke (cr);
		cairo_restore (cr);
	}
	else
	{
		if (debug) printf ("Transparent border\n");
		cairo_new_path (cr);
	}

	// Paint shade gradient
	{
		cairo_pattern_t *gradient = wave_mesh_create (aspect, 1);
		cairo_pattern_t *w = cairo_pattern_create_for_surface (waved_flag);

		cairo_save (cr);
		cairo_set_source (cr, gradient);

		cairo_set_operator (cr, CAIRO_OPERATOR_SOFT_LIGHT);
		cairo_mask (cr, w);

		cairo_restore (cr);

		cairo_pattern_destroy (w);
	}

	if (debug)
	{
		/* Draw mesh points. */
		cairo_save (cr);
		cairo_scale (cr, SIZE/128.*SCALE, SIZE/128.*SCALE);
		cairo_set_source_rgba (cr, .5,.0,.0,.9);
		cairo_set_line_cap (cr, CAIRO_LINE_CAP_ROUND);
		for (unsigned int i = 0; i < sizeof (mesh_points) / sizeof (mesh_points[0]); i++)
		{
			cairo_move_to (cr, M(i));
			cairo_rel_line_to (cr, 0, 0);
		}
		cairo_set_line_width (cr, 2);
		cairo_stroke (cr);
		for (unsigned int i = 0; i < 4; i++)
		{
			cairo_move_to (cr, M(2*i));
			cairo_line_to (cr, M(2*i+1));
			cairo_move_to (cr, M(2*i));
			cairo_line_to (cr, M(7 - 2*i));
		}
		cairo_set_line_width (cr, .5);
		cairo_stroke (cr);
		cairo_restore (cr);
	}

	if (!debug)
	{
		/* Scale down, 2x at a time, to get best downscaling, because cairo's
		 * downscaling is crap... :( */
		unsigned int scale = SCALE;
		while (scale > 1)
		{
			cairo_surface_t *old_surface, *new_surface;

			old_surface = cairo_surface_reference (cairo_get_target (cr));
			assert (scale % 2 == 0);
			scale /= 2;
			cairo_destroy (cr);
			new_surface = cairo_image_surface_create (CAIRO_FORMAT_ARGB32, (SIZE+2*MARGIN)*scale, (SIZE+2*MARGIN)*scale);
			cr = cairo_create (new_surface);
			cairo_scale (cr, .5, .5);
			cairo_set_source_surface (cr, old_surface, 0, 0);
			cairo_paint (cr);
			cairo_surface_destroy (old_surface);
			cairo_surface_destroy (new_surface);
		}
	}

	*out = '\0';
	strcat (out, out_prefix);
        // diff from upstream. we call this a bit differently, filename might not be in cwd.

        // basename wants a non-const argument.  The problem here is paths that end in a
        // slash, POSIX basename removes them while GNU just returns a pointer to that
        // slash.  Since this is supposed to be a filename such input is illegal for us.
        // We're already not checking for overflow of the output buffer anyway...
	strcat (out, basename((char *) filename));

	cairo_surface_write_to_png (cairo_get_target (cr), out);
	cairo_destroy (cr);
	if (wave_path != standard_wave_path)
		cairo_path_destroy (wave_path);
	if (wave_surface != standard_wave_surface)
		cairo_surface_destroy (wave_surface);
}

int
main (int argc, char **argv)
{
	const char *out_prefix;

	if (argc < 3)
	{
	  fprintf (stderr, "Usage: waveflag [-debug] out-prefix [in.png]...\n");
	  return 1;
	}

	if (!strcmp (argv[1], "-debug"))
	{
	  debug = 1;
	  argc--, argv++;
	}

	out_prefix = argv[1];
	argc--, argv++;

	for (argc--, argv++; argc; argc--, argv++)
		wave_flag (*argv, out_prefix);

	return 0;
}
