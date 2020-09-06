from tensorflow import keras


def build_model():
    model = keras.models.Sequential(layers=[
        keras.layers.Dense(128, activation=keras.activations.relu, input_shape=(8,)),
        keras.layers.Dense(128, activation=keras.activations.relu),
        keras.layers.Dense(128, activation=keras.activations.relu),
        keras.layers.Dense(128, activation=keras.activations.relu),
        keras.layers.Dense(128, activation=keras.activations.relu),
        keras.layers.Dense(128, activation=keras.activations.relu),
        keras.layers.Dropout(rate=0.01),
        keras.layers.Dense(3, activation=keras.activations.linear)
    ])

    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.0001),
                  loss=keras.losses.mean_squared_error)

    return model
