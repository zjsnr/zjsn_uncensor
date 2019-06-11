function FindProxyForURL(url, host)
{
    proxy = "PROXY do.gwy15.com:14514";
    if (shExpMatch(host, "version.jr.moefantasy.com"))
        return proxy;
    if (shExpMatch(host,"version.channel.jr.moefantasy.com"))
	    return proxy;
    return "DIRECT";
}
