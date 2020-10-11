# For cython to generate python library

default: pysccd

pysccd: setup.py pysccd.pyx libsccd.so
	python3 setup.py build_ext --inplace && rm -f pysccd.c && rm -Rf build
	# cp pysccd*.so $(PYTHON_SCCDPROJECT_DIR)
	# cp libsccd.so $(PYTHON_LIB_DIR)
	# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(PYTHON_SCCDPROJECT_DIR)
	# cp pysccd.pyx $(PYTHON_PACKAGE_DIR)
clean:
	rm pysccd*.so
	# rm $(PYTHON_SCCDPROJECT_DIR)/pysccd*.so
	# rm libsccd.so
	# rm $(PYTHON_SCCDPROJECT_DIR)/libsccd.so
