#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <unistd.h>
#include <sys/stat.h>
#include <limits.h>

#define MAX_FILE_SIZE (10 * 1024 * 1024)
#define MAX_RESOLUTION 8000
#define MAX_OUTPUT_BUFFER (100 * 1024 * 1024)

#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION
#define STB_IMAGE_RESIZE2_IMPLEMENTATION

#include "stb_image.h"
#include "stb_image_write.h"
#include "stb_image_resize2.h"


enum ResizeMode {
    MODE_STRETCH,
    MODE_FIT,
    MODE_FILL
};


int check_file(const char *path)
{
    struct stat st;

    if (access(path, F_OK) != 0) {
        fprintf(stderr, "Error: input file not found\n");
        return -1;
    }

    if (stat(path, &st) != 0) {
        perror("stat");
        return -1;
    }

    if (!S_ISREG(st.st_mode)) {
        fprintf(stderr, "Error: input must be a regular file\n");
        return -1;
    }

    if (st.st_size > MAX_FILE_SIZE) {
        fprintf(stderr, "Error: file exceeds 10MB limit\n");
        return -1;
    }

    return 0;
}


void enforce_jpg_extension(const char *input, char *output, size_t size)
{
    const char *dot = strrchr(input, '.');

    if (dot && (strcasecmp(dot, ".jpg") == 0 || strcasecmp(dot, ".jpeg") == 0)) {
        snprintf(output, size, "%s", input);
        return;
    }

    snprintf(output, size, "%s.jpg", input);
}


int parse_int(const char *str, int *value)
{
    char *end;
    long v = strtol(str, &end, 10);

    if (*end != '\0')
        return -1;

    *value = (int)v;
    return 0;
}


/* compute aspect-ratio based size */
void compute_fit(int src_w, int src_h, int *dst_w, int *dst_h)
{
    float ratio = (float)src_w / src_h;

    if (*dst_w / (float)*dst_h > ratio)
        *dst_w = *dst_h * ratio;
    else
        *dst_h = *dst_w / ratio;
}


void compute_fill(int src_w, int src_h, int *dst_w, int *dst_h)
{
    float ratio = (float)src_w / src_h;

    if (*dst_w / (float)*dst_h < ratio)
        *dst_w = *dst_h * ratio;
    else
        *dst_h = *dst_w / ratio;
}


int resize_image(const char *input_path,
                 const char *output_path,
                 int new_w,
                 int new_h,
                 int allow_upscale,
                 int mode)
{
    int width, height, channels;

    unsigned char *img = stbi_load(input_path, &width, &height, &channels, 0);

    if (!img) {
        fprintf(stderr, "Error: corrupted or unsupported image\n");
        return -1;
    }

    if (channels < 1 || channels > 4) {
        fprintf(stderr, "Error: unsupported channel count\n");
        stbi_image_free(img);
        return -1;
    }

    if (width > MAX_RESOLUTION || height > MAX_RESOLUTION) {
        fprintf(stderr, "Error: image resolution too large\n");
        stbi_image_free(img);
        return -2;
    }

    if (!allow_upscale && (new_w > width || new_h > height)) {
        fprintf(stderr, "Error: upscaling not allowed\n");
        stbi_image_free(img);
        return -3;
    }

    int target_w = new_w;
    int target_h = new_h;

    if (mode == MODE_FIT)
        compute_fit(width, height, &target_w, &target_h);

    if (mode == MODE_FILL)
        compute_fill(width, height, &target_w, &target_h);


    if ((size_t)target_w > SIZE_MAX / (size_t)target_h / (size_t)channels) {
        fprintf(stderr, "Error: image size overflow\n");
        stbi_image_free(img);
        return -4;
    }

    size_t size = (size_t)target_w * target_h * channels;

    if (size > MAX_OUTPUT_BUFFER) {
        fprintf(stderr, "Error: output image too large\n");
        stbi_image_free(img);
        return -5;
    }

    unsigned char *resized = malloc(size);

    if (!resized) {
        fprintf(stderr, "Error: memory allocation failed\n");
        stbi_image_free(img);
        return -6;
    }

    if (!stbir_resize_uint8_linear(
            img, width, height, 0,
            resized, target_w, target_h, 0,
            (stbir_pixel_layout)channels))
    {
        fprintf(stderr, "Error during resize\n");
        free(resized);
        stbi_image_free(img);
        return -7;
    }

    int write_channels = channels >= 3 ? 3 : channels;

    if (!stbi_write_jpg(output_path, target_w, target_h, write_channels, resized, 85)) {
        fprintf(stderr, "Error writing output image\n");
        free(resized);
        stbi_image_free(img);
        return -8;
    }

    printf("[SUCCESS] %s (%dx%d)\n", output_path, target_w, target_h);

    free(resized);
    stbi_image_free(img);

    return 0;
}


void print_help()
{
    printf("Image Resize Utility\n\n");
    printf("Usage:\n");
    printf("resize input.jpg output.jpg width height [options]\n\n");

    printf("Options:\n");
    printf("  --allow-upscale\n");
    printf("  --fit       keep aspect ratio (fit inside)\n");
    printf("  --fill      fill area and crop overflow\n");
    printf("  --stretch   ignore aspect ratio (default)\n");
    printf("  --help\n");
    printf("  --version\n");
}


int main(int argc, char *argv[])
{

    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        print_help();
        return 0;
    }

    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        printf("resize version 1.1\n");
        return 0;
    }

    if (argc < 5) {
        print_help();
        return 1;
    }

    const char *input = argv[1];

    char output[512];
    enforce_jpg_extension(argv[2], output, sizeof(output));

    int width, height;

    if (parse_int(argv[3], &width) != 0 ||
        parse_int(argv[4], &height) != 0)
    {
        fprintf(stderr, "Error: width and height must be valid numbers\n");
        return 1;
    }

    int allow_upscale = 0;
    int mode = MODE_STRETCH;

    for (int i = 5; i < argc; i++) {

        if (strcmp(argv[i], "--allow-upscale") == 0)
            allow_upscale = 1;

        else if (strcmp(argv[i], "--fit") == 0)
            mode = MODE_FIT;

        else if (strcmp(argv[i], "--fill") == 0)
            mode = MODE_FILL;

        else if (strcmp(argv[i], "--stretch") == 0)
            mode = MODE_STRETCH;
    }

    if (width <= 0 || height <= 0) {
        fprintf(stderr, "Error: width and height must be positive\n");
        return 1;
    }

    if (width > MAX_RESOLUTION || height > MAX_RESOLUTION) {
        fprintf(stderr, "Error: requested size exceeds allowed limit\n");
        return 1;
    }

    if (check_file(input) != 0)
        return 1;

    return resize_image(input, output, width, height, allow_upscale, mode);
}
