# We create a simple CNN architecture for image classification
# Architecture inspired by:
# https://colab.research.google.com/github/tensorflow/docs/blob/master/site/en/tutorials/images/classification.ipynb#scrollTo=L1WtoaOHVrVh

from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten, MaxPooling2D
from tensorflow.keras.callbacks import LearningRateScheduler
from tensorflow.keras.optimizers import SGD
from pipeline.optimisation.learning_rate_schedulers import StepDecay, PolynomialDecay
from pipeline.optimisation.one_cycle_lr.lr_finder import LRFinder
from pipeline.optimisation.one_cycle_lr.one_cycle_scheduler import OneCycleScheduler

def train_cnn(
        height,
        width,
        num_classes,
        batch_size,
        epochs,
        learning_rate,
        schedule_type,
        find_lr,
        train_gen,
        val_gen,
        num_start_filters,
        kernel_size,
        fcl_size):

    # Store the number of epochs to train for in a convenience variable,
    # then initialize the list of callbacks and learning rate scheduler
    # to be used
    callbacks = []
    schedule = None
    
    if find_lr != True:
        # check to see if step-based learning rate decay should be used
        if schedule_type == "step":
    	    print("[INFO] using 'step-based' learning rate decay...")
    	    schedule = StepDecay(initAlpha=1e-1, factor=0.25, dropEvery=int(epochs/5))
 
        # check to see if linear learning rate decay should should be used
        elif schedule_type == "linear":
            print("[INFO] using 'linear' learning rate decay...")
            schedule = PolynomialDecay(maxEpochs=epochs, initAlpha=1e-1, power=1)
    
        # check to see if a polynomial learning rate decay should be used
        elif schedule_type == "poly":
            print("[INFO] using 'polynomial' learning rate decay...")
            schedule = PolynomialDecay(maxEpochs=epochs, initAlpha=1e-1, power=5)

        elif schedule_type == "one_cycle":
            print("[INFO] using 'one cycle' learning...")
            schedule = OneCycleScheduler(learning_rate)
            callbacks = [schedule]

        # if the learning rate schedule is not empty, add it to the list of
        # callbacks
        if schedule_type != "none" and schedule_type != "one_cycle":
	        callbacks = [LearningRateScheduler(schedule)]

        # initialize the decay for the optimizer
        decay = 0.0
 
        # if we are using Keras' "standard" decay, then we need to set the
        # decay parameter
        if schedule_type == "standard":
        	print("[INFO] using 'keras standard' learning rate decay...")
        	decay = 1e-1 / epochs
 
        # otherwise, no learning rate schedule is being used
        elif schedule_type == "none":
        	print("[INFO] no learning rate schedule being used")
    else:
        print("[INFO] Finding learning rate...")

    # Instantiate Sequential API
    model = Sequential([
        # Use 16 3x3 kernels with ReLU after.
        Conv2D(num_start_filters, kernel_size, padding='same', activation='relu', input_shape=(height,width,3)),
        # Pooling layer
        MaxPooling2D(),
        # Use 32 3x3 kernels with ReLU after. Notice this is double the last layer.
        Conv2D(num_start_filters*2, kernel_size, padding='same', activation='relu'),
        # Pooling layer
        MaxPooling2D(),
        # Use 64 3x3 kernels with ReLU after. Notice this is double the last layer.
        Conv2D(num_start_filters*4, kernel_size, padding='same', activation='relu'),
        # Pooling layer
        MaxPooling2D(),
        # Flatten for use with fully-connected layers
        Flatten(),
        # Fully connected layer with 512 neurons
        Dense(fcl_size, activation='relu'),
        # Output layer
        Dense(num_classes, activation='softmax')
    ])

    if schedule_type != "one_cycle" and find_lr != True:
        # initialize optimizer and model, then compile it
        opt = SGD(lr=learning_rate, momentum=0.9, decay=decay)
    else:
        opt = SGD()
    
    # We now compile the MLP model to specify the loss function
    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer=opt,
	    metrics=["accuracy"])

    if find_lr == True:
        lr_finder = LRFinder(model)
        lr_finder.find(train_gen)
        return lr_finder
    else:
        # Training and evaluating the CNN model
        history = model.fit(
            train_gen,
            steps_per_epoch=train_gen.samples // batch_size,
            validation_data=val_gen,
            validation_steps=val_gen.samples // batch_size,
            callbacks=callbacks,
            epochs=epochs)
        return model, history, schedule