function FindProxyForURL(url, host)
{
    proxy = "PROXY float.gwy15.com:14514";

    if (shExpMatch(host, "version.jr.moefantasy.com"))
        return proxy;
    if (shExpMatch(host, "version.channel.jr.moefantasy.com"))
	    return proxy;
    return "DIRECT";
}
