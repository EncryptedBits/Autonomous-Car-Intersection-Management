from __future__ import print_function
import numpy as np
import tensorflow as tf
import Configurations
import simulator_random as environment
from six.moves import range

# Variables from simulator
no_hidden_nodes = 1024

graph = tf.Graph()
with graph.as_default():
    size_of_state = 4 * Configurations.NO_OF_LANES * (2 + Configurations.NO_OF_LANES)
    no_of_action = pow(2, 4 * Configurations.NO_OF_LANES)

    # training and validation data initialisation...
    tf_train_datasets = tf.placeholder(tf.float32, shape=(1, size_of_state))
    tf_train_labels = tf.placeholder(tf.float32, shape=(1, no_of_action))
    beta_regul = tf.placeholder(tf.float32)

    # weights and biases initialisation...
    l1_weights = tf.Variable(tf.truncated_normal([size_of_state, no_hidden_nodes]))
    l1_biases = tf.Variable(tf.zeros([no_hidden_nodes]))
    l2_weights = tf.Variable(tf.truncated_normal([no_hidden_nodes, no_hidden_nodes]))
    l2_biases = tf.Variable(tf.zeros([no_hidden_nodes]))
    l3_weights = tf.Variable(tf.truncated_normal([no_hidden_nodes, no_of_action]))
    l3_biases = tf.Variable(tf.zeros([no_of_action]))

    # training mechanism or neural network building
    layer1_train = tf.nn.relu(tf.matmul(tf_train_datasets, l1_weights) + l1_biases)
    layer2_train = tf.nn.relu(tf.matmul(layer1_train, l2_weights) + l2_biases)
    logits = tf.matmul(layer2_train, l3_weights) + l3_biases

    # loss function initialisation
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=tf_train_labels)) + \
           beta_regul * (tf.nn.l2_loss(l1_weights) + tf.nn.l2_loss(l2_weights) + tf.nn.l2_loss(l3_weights))

    # optimizer
    optimizer = tf.train.GradientDescentOptimizer(0.001).minimize(loss)

    # prediction for training, validation and test data
    train_prediction = tf.nn.softmax(logits)


num_iters = 7001

with tf.Session(graph=graph, config=tf.ConfigProto(log_device_placement=True)) as session:
    print("Training started")
    tf.global_variables_initializer().run()
    print("Varibles Initialized!...")
    for epoch in xrange(num_iters):

        #batch_data : The state of environment
        #batch_labels : The real action in one-hot encoding

        batch_data = environment.get_state()
        batch_labels = environment.get_real_action()

        feed_dict = {tf_train_datasets: batch_data, tf_train_labels: batch_labels, beta_regul: regul}

        _, l, prediction = session.run([optimizer, loss, train_prediction], feed_dict=feed_dict)
