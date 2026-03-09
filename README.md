# Image Resize Utility

A lightweight **C command-line image resizing tool** built using the **stb image libraries**.

This utility provides **safe, high-quality image resizing** with built-in protections for:

* oversized files
* invalid input
* memory abuse
* unsafe resolutions

It supports **aspect-ratio aware resizing** similar to professional tools like ImageMagick.

---

# Features

* High-quality resizing using `stb_image_resize2`
* Aspect-ratio aware resize modes
* Secure input validation
* File size protection
* Resolution protection
* Memory allocation safety
* Optional upscaling
* Simple CLI interface

---

# Resize Modes

| Mode        | Description                               |
| ----------- | ----------------------------------------- |
| `--stretch` | Resize ignoring aspect ratio              |
| `--fit`     | Fit image inside the requested size       |
| `--fill`    | Fill the requested size and crop overflow |

---

# Supported Input Formats

Supported via **stb_image**:

* JPEG
* PNG
* BMP
* TGA
* GIF
* PSD
* HDR
* PIC
* PNM

Output format:

```
JPEG (.jpg)
```

---

# Installation

## Requirements

* Linux
* GCC compiler

---

## Compile

```bash
gcc resize.c -o resize -lm
```

The `-lm` flag links the **math library**, required by the stb libraries.

---

# Usage

```bash
resize input.jpg output.jpg width height [options]
```

---

# Examples

## Basic Resize

```bash
resize input.jpg output.jpg 300 300
```

Default mode is **stretch**.

---

## Fit Inside Box

```bash
resize input.jpg output.jpg 300 300 --fit
```

Image will fit **inside 300x300 without distortion**.

Example:

```
Original: 1920x1080
Output:   300x168
```

---

## Fill and Crop

```bash
resize input.jpg output.jpg 300 300 --fill
```

Image fills entire **300x300 area**.

Example:

```
Original: 1920x1080
Output:   300x300 (cropped)
```

---

## Allow Upscaling

```bash
resize input.jpg output.jpg 1920 1080 --allow-upscale
```

By default, enlarging images is **disabled**.

---

# Help

```bash
resize --help
```

---

# Version

```bash
resize --version
```

---

# Security Protections

The program includes several protections to prevent misuse.

---

## File Size Limit

Maximum input file size:

```
10MB
```

Example error:

```
Error: file exceeds 10MB limit
```

---

## Maximum Resolution

Maximum allowed resolution:

```
8000 x 8000
```

Example error:

```
Error: image resolution too large
```

---

## Output Buffer Protection

Maximum output buffer:

```
100MB
```

This prevents memory exhaustion attacks.

Example error:

```
Error: output image too large
```

---

## Input Validation

Invalid commands are rejected.

Example:

```
resize input.jpg output.jpg 0 0
```

Error:

```
Error: width and height must be positive
```

---

# Safety Checks Implemented

| Protection                       | Description                 |
| -------------------------------- | --------------------------- |
| File existence check             | Prevents invalid file paths |
| Regular file validation          | Blocks device files         |
| File size limit                  | Prevents large uploads      |
| Resolution limit                 | Prevents huge images        |
| Overflow-safe memory calculation | Prevents integer overflow   |
| Output buffer limit              | Prevents memory abuse       |
| Channel validation               | Ensures valid image format  |

---

# Example Server Usage

This tool can be used in **backend services or APIs**.

Example:

```bash
resize /tmp/input.jpg /tmp/output.jpg 300 300 --fit
```

A web server could:

1. Upload an image to `/tmp`
2. Run the resize command
3. Return the processed image

---

# Example Bulk Usage

Resize multiple images using a shell loop:

```bash
for img in *.jpg; do
    resize "$img" "resized_$img" 300 300 --fit
done
```

---

# Libraries Used

This project uses the following public domain libraries:

* `stb_image`
* `stb_image_write`
* `stb_image_resize2`

These libraries are written by **Sean Barrett** and released under permissive licenses.

---

# Author

Image Resize Utility
Written in **C** for fast and secure image processing.

---

