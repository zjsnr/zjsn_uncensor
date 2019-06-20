function FindProxyForURL(url, host)
{
    proxy = "PROXY do.gwy15.com:14514";
    if (shExpMatch(host, "bshot.moefantasy.com"))
        return proxy;
    if (shExpMatch(host,"bshot.moefantasy.com"))
	    return proxy;
    return "DIRECT";
}
