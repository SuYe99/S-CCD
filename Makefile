# Configuration for mac
SRC_DIR = .
DST_DIR = ./build-CCDC_C
BIN ?= ./tool/python
GSL_SCI_INC ?= /usr/include/gsl
GSL_SCI_LIB ?= /usr/local/lib
ESPAINC ?=

# Set up compile options
CC = gcc
FORTRAN = gfortran
RM = rm -f
MV = mv
CGLAGS = -fPIC -Wall -Wextra -g 
LDFLAGS = -shared
FFLAGS = -g
LFLAGS = -fopenmp

# Define the include files
INC = $(wildcard $(SRC_DIR)/*.h)
INCDIR  = -I. -I/$(DST_DIR) -I$(SRC_DIR) -I$(GSL_SCI_INC) 
NCFLAGS = $(EXTRA) $(INCDIR)

# Define the source code and object files
#SRC = input.c 2d_array.c ccdc.c utilities.c misc.c
SRC = cold.c input.c 2d_array.c utilities.c misc.c multirobust.c output.c s_ccd.c KFAS.c lbfgs.c distribution_math.c
OBJ = $(SRC:.c=.o)

# Define the object libraries
LIB = -L$(GSL_SCI_LIB) -lz -lpthread -lgsl -lgslcblas -lgfortran -lm -fopenmp 

# Define the executable
TARGET_LIB = libsccd.so

# Target for the executable
all: ${TARGET_LIB}

$(TARGET_LIB): $(OBJ) GLMnet $(INC)
	$(CC) $(LFLAGS) $(CGLAGS) $(NCFLAGS) $(INCDIR) -o ${TARGET_LIB} $(OBJ) GLMnet.o $(LIB) $(LDFLAGS)

GLMnet: $(SRC) GLMnet.f
	$(FORTRAN) $(FFLAGS) -c GLMnet.f -o GLMnet.o

clean: 
	$(RM) $(BIN)/$(TARGET_LIB)
	$(RM) $(BIN)/variables
	$(RM) $(DST_DIR)/*.o
	$(RM) $(DST_DIR)/*.a

$(BUILD):
	mkdir -p $(DST_DIR)

$(BIN):
	mkdir -p $(BIN)


install: $(BUILD)
	# $(BIN)
	mv $(TARGET_LIB) $(BIN)
	mv $(OBJ) $(DST_DIR)
	cp variables $(BIN)


$(OBJ): $(INC)

.c.o:
	$(CC) $(LFLAGS) -fPIC $(NCFLAGS) $(INCDIR) -c $<


