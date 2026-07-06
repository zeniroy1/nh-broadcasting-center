using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;

namespace HamShare.Receiver.Services;

public static class NetworkAddress
{
    public static IReadOnlyList<IPAddress> GetLocalIpv4Addresses()
        => NetworkInterface.GetAllNetworkInterfaces()
            .Where(adapter => adapter.OperationalStatus == OperationalStatus.Up
                && adapter.NetworkInterfaceType is not NetworkInterfaceType.Loopback)
            .SelectMany(adapter => adapter.GetIPProperties().UnicastAddresses)
            .Where(address => address.Address.AddressFamily == AddressFamily.InterNetwork
                && !IPAddress.IsLoopback(address.Address))
            .Select(address => address.Address)
            .Distinct()
            .ToArray();
}
