#RPC server for Erlang and OTP in action


To build this code, run the following command:

    erlc -o ./ebin ./src/*.erl

To run the program, first start Erlang like this:

    erl -pa ./ebin

Then, run the following in the Erlang shell:

    1> application:start(tcp_rpc).
    ok
    2> 

After that, open another terminal window and use telnet
to connect to the application, like this:

    __$ telnet localhost 1055__
    Trying 127.0.0.1...
    Connected to localhost.localdomain.
    Escape character is '^]'.
    lists:reverse([1,2,3]).
    [3,2,1]
    init:stop().
    ok
    Connection closed by foreign host.
