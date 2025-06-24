# Compiler
CC = gcc # Atau clang jika Anda lebih suka

# Project Folders
SRC_DIR = src
LIB_DIR = lib
INCLUDE_DIR = include
BUILD_DIR = build

# Source Files (Hanya main.c, raygui.c TIDAK perlu di sini lagi)
SRCS = $(SRC_DIR)/main.c \
       $(SRC_DIR)/function/adlink_adc_dumy.c \
       $(SRC_DIR)/ui/wave_display.c \
       $(SRC_DIR)/ui/ppi_display.c \
       $(SRC_DIR)/ui/ppi_speed_slider.c

# Object Files
OBJS = $(patsubst $(SRC_DIR)/%.c, $(BUILD_DIR)/%.o, $(SRCS))

# Executable Name
TARGET = main

# Raylib Paths
RAYLIB_PATH = $(LIB_DIR)/raylib
RAYLIB_SRC_PATH = $(RAYLIB_PATH)/src
RAYLIB_INCLUDE_PATH = $(RAYLIB_PATH)/src # Atau $(RAYLIB_PATH)/include jika ada
RAYLIB_LIB_PATH = $(RAYLIB_PATH)/src # Lokasi libraylib.a

# Raygui Paths (Hanya untuk include path, tidak perlu lib atau src file)
RAYGUI_PATH = $(LIB_DIR)/raygui
RAYGUI_INCLUDE_PATH = $(RAYGUI_PATH)/src # Lokasi raygui.h

# Compiler Flags
CFLAGS = -I$(RAYLIB_INCLUDE_PATH) \
         -I$(RAYGUI_INCLUDE_PATH) \
         -I$(INCLUDE_DIR) \
         -Wall -std=c99

# Linker Flags (Sesuaikan dengan OS Anda)
# Untuk Linux/macOS:
LDFLAGS = -L$(RAYLIB_LIB_PATH) -lraylib -lGL -lm -lpthread -ldl -lrt -lX11

# Untuk Windows (MinGW-w64):
# LDFLAGS = -L$(RAYLIB_LIB_PATH) -lraylib -lopengl32 -lgdi32 -lwinmm -luser32 -static -std=c99 -Wall

# Default target
all: $(BUILD_DIR) $(TARGET)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $@ $(LDFLAGS)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# Clean up
clean:
	rm -rf $(BUILD_DIR) $(TARGET)

# Build Raylib (optional, can be run once manually)
build_raylib:
	cd $(RAYLIB_SRC_PATH) && make PLATFORM=PLATFORM_DESKTOP

.PHONY: all clean build_raylib